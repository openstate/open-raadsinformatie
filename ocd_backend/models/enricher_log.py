from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.pool import StaticPool

from ocd_backend import settings
from ocd_backend.models.postgres_models import EnricherLogModel
from ocd_backend.log import get_source_logger

log = get_source_logger('enricher_log')


class EnricherLog(object):

    def __init__(self):
        self.connection_string = 'postgresql://%s:%s@%s/%s' % (
                                    settings.POSTGRES_USERNAME,
                                    settings.POSTGRES_PASSWORD,
                                    settings.POSTGRES_HOST,
                                    settings.POSTGRES_DATABASE)
        self.engine = create_engine(self.connection_string, poolclass=StaticPool)
        self.Session = sessionmaker(bind=self.engine)

    def check(self, resource_id, enricher_class, task):
        """
        Checks whether a particular enricher task has already been completed for a resource.
        """

        session = self.Session()
        try:
            enricher_log = session.query(EnricherLogModel).filter(EnricherLogModel.resource_id == resource_id,
                                                                  EnricherLogModel.enricher_class == enricher_class,
                                                                  EnricherLogModel.task == task).one()
            return True
        except MultipleResultsFound:
            log.error('Multiple enricher logs found for resource id %s and task "%s.%s"' % (resource_id,
                                                                                            enricher_class,
                                                                                            task))
        except NoResultFound:
            return False
        finally:
            session.close()

    def insert(self, resource_id, enricher_class, task):
        """
        Inserts an entry into the enricher log.
        """

        session = self.Session()
        enricher_log = EnricherLogModel(resource_id=resource_id, enricher_class=enricher_class, task=task)
        session.add(enricher_log)
        session.commit()
        session.close()
