from sqlalchemy import create_engine, Sequence
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import exists

from ocd_backend import settings
from ocd_backend.models.postgres_models import Resource
from ocd_backend.models.definitions import Ori
from ocd_backend.models.misc import Uri


class PostgresDatabase(object):

    def __init__(self):
        self.connection_string = 'postgresql://%s:%s@%s/%s' % (
                                    settings.POSTGRES_USERNAME,
                                    settings.POSTGRES_PASSWORD,
                                    settings.POSTGRES_HOST,
                                    settings.POSTGRES_DATABASE)
        self.engine = create_engine(self.connection_string)
        self.session = sessionmaker(bind=self.engine)()

    def get_ori_identifier(self, iri):
        statement = exists().where(Resource.iri == iri)
        for ori_id, in self.session.query(Resource.ori_id).filter(statement):
            if ori_id:
                return Uri(Ori, ori_id)
            else:
                raise AttributeError()

    def generate_ori_identifier(self):
        return Uri(Ori, self.engine.execute(Sequence('ori_id_seq')))
