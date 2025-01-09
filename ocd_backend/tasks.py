from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.es import elasticsearch as es
from ocd_backend.log import get_source_logger
from ocd_backend.models.postgres_database import PostgresDatabase
from ocd_backend.models.postgres_models import ItemHash
from ocd_backend.models.serializers import PostgresSerializer
from ocd_backend.utils.misc import iterate
from ocd_backend.settings import AUTORETRY_EXCEPTIONS, RETRY_MAX_RETRIES, AUTORETRY_RETRY_BACKOFF, AUTORETRY_RETRY_BACKOFF_MAX

log = get_source_logger('ocd_backend.tasks')


class BaseCleanup(celery_app.Task):
    ignore_result = True

    def start(self, *args, **kwargs):
        run_identifier = kwargs.get('run_identifier')
        run_identifier_chains = '{}_chains'.format(run_identifier)
        self._remove_chain(run_identifier_chains, kwargs.get('chain_id'))

        run_result = self.backend.get(run_identifier)
        if isinstance(run_result, bytes):
            run_result = run_result.decode()
        if self.backend.get_set_cardinality(run_identifier_chains) < 1 and run_result == 'done':
            self.backend.remove(run_identifier_chains)
            self.run_finished(**kwargs)
        else:
            # If the extractor is still running, extend the lifetime of the
            # identifier
            self.backend.update_ttl(run_identifier, settings.CELERY_CONFIG
                                    .get('CELERY_TASK_RESULT_EXPIRES', 1800))

    def _remove_chain(self, run_identifier, value):
        self.backend.remove_value_from_set(run_identifier, value)

    def run_finished(self, run_identifier, **kwargs):
        raise NotImplementedError('Cleanup is highly dependent on what you use '
                                  'for storage, so this should be implemented '
                                  'in a subclass.')


class CleanupElasticsearch(BaseCleanup):
    def run_finished(self, run_identifier, **kwargs):
        current_index_name = kwargs.get('current_index_name')
        new_index_name = kwargs.get('new_index_name')
        alias = kwargs.get('index_alias')

        result = 'Finished run {}. Removing alias "{}" from "{}", and ' \
                 'applying it to "{}"'.format(run_identifier, alias,
                                              current_index_name,
                                              new_index_name)
        log.info(result)

        actions = {
            'actions': [
                {
                    'remove': {
                        'index': current_index_name,
                        'alias': alias
                    }
                },
                {
                    'add': {
                        'index': new_index_name,
                        'alias': alias
                    }
                }
            ]
        }

        # Set alias to new index
        es.indices.update_aliases(body=actions)

        # Remove old index
        if current_index_name != new_index_name:
            es.indices.delete(index=current_index_name)

        return result


class DummyCleanup(BaseCleanup):
    def run_finished(self, run_identifier, **kwargs):
        log.info(f'Finished run {run_identifier}')


class Finalizer(celery_app.Task):
    """
    This task runs after the ETL steps are processed succesfully.
    It stores a hash of the input values (of a Meeting, Report, Person etc) in the ItemHash table.
    Each ETL pipeline starts by checking this table - if a record exists and the hash value is the
    same, processing can be skipped.
    """
    def __init__(self):
        database = PostgresDatabase(serializer=PostgresSerializer)
        self.session = database.Session()

    def start(self, *args, **kwargs):
        self.hash_for_item = kwargs['hash_for_item']

        if not self.hash_for_item:
            return

        self.set_processed()

    def set_processed(self):
        old_item = self.session.query(ItemHash).filter(ItemHash.item_id == self.hash_for_item.hash_key).first()

        if old_item:
            if old_item.item_hash != self.hash_for_item.hash_value: 
                old_item.item_hash = self.hash_for_item.hash_value
                self.session.commit()
                self.session.flush()
        else:
            new_item = ItemHash(item_id=self.hash_for_item.hash_key, item_hash=self.hash_for_item.hash_value)
            self.session.add(new_item)
            self.session.commit()
            self.session.flush()


@celery_app.task(bind=True, base=CleanupElasticsearch, autoretry_for=AUTORETRY_EXCEPTIONS,
                 retry_backoff=AUTORETRY_RETRY_BACKOFF, max_retries=RETRY_MAX_RETRIES, retry_backoff_max=AUTORETRY_RETRY_BACKOFF_MAX)
def cleanup_elasticsearch(self, *args, **kwargs):
    return self.start(*args, **kwargs)


@celery_app.task(bind=True, base=DummyCleanup, autoretry_for=AUTORETRY_EXCEPTIONS,
                 retry_backoff=AUTORETRY_RETRY_BACKOFF, max_retries=RETRY_MAX_RETRIES, retry_backoff_max=AUTORETRY_RETRY_BACKOFF_MAX)
def dummy_cleanup(self, *args, **kwargs):
    return self.start(*args, **kwargs)

@celery_app.task(bind=True, base=Finalizer, autoretry_for=AUTORETRY_EXCEPTIONS,
                 retry_backoff=AUTORETRY_RETRY_BACKOFF, max_retries=RETRY_MAX_RETRIES, retry_backoff_max=AUTORETRY_RETRY_BACKOFF_MAX)
def finalizer(self, *args, **kwargs):
    return self.start(*args, **kwargs)
