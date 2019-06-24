from sqlalchemy import create_engine, Sequence
from sqlalchemy.orm import sessionmaker

from ocd_backend import settings
from ocd_backend.models.postgres_models import Source, Resource
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
        self.Session = sessionmaker(bind=self.engine)

    def get_ori_identifier(self, iri):
        session = self.Session()
        for resource in session.query(Resource).filter(Resource.iri == iri):
            if resource:
                session.close()
                return Uri(Ori, resource.ori_id)
            else:
                session.close()
                raise AttributeError()

    def generate_ori_identifier(self, iri=None):
        session = self.Session()
        new_id = self.engine.execute(Sequence('ori_id_seq'))
        new_identifier = Uri(Ori, new_id)
        # IRI can be None in rare cases, like EventConfirmed nodes
        if iri:
            source = Source(iri=iri, resources=[Resource(id=new_id, ori_id=new_id, iri=iri),])
            session.add(source)
        session.commit()
        session.close()
        return new_identifier
