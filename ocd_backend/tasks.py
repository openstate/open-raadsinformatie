import redis

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.es import elasticsearch as es
from ocd_backend.log import get_source_logger
from ocd_backend.models.postgres_database import PostgresDatabase
from ocd_backend.models.postgres_models import ItemHash
from ocd_backend.models.serializers import PostgresSerializer
from ocd_backend.utils.indexed_file import IndexedFile
from ocd_backend.utils.misc import iterate
from ocd_backend.settings import AUTORETRY_EXCEPTIONS, RETRY_MAX_RETRIES, AUTORETRY_RETRY_BACKOFF, AUTORETRY_RETRY_BACKOFF_MAX
from ocd_backend.settings import REDIS_HOST, REDIS_PORT

log = get_source_logger('ocd_backend.tasks')


class BaseCleanup(celery_app.Task):
    ignore_result = True

    def start(self, *args, **kwargs):
        source_run_identifier = kwargs.get('source_run_identifier')
        run_identifier = kwargs.get('run_identifier')
        run_identifier_chains = '{}_chains'.format(run_identifier)
        self._remove_chain(source_run_identifier, kwargs.get('chain_id'))
        self._remove_chain(run_identifier_chains, kwargs.get('chain_id'))

        run_result = self.backend.get(run_identifier)
        if isinstance(run_result, bytes):
            run_result = run_result.decode()
        if self.backend.get_set_cardinality(run_identifier_chains) < 1 and run_result != 'running':
            # All tasks for an entity (e.g. meetings or committees) have finished
            self.backend.remove(run_identifier_chains)
        else:
            # If the extractor is still running, extend the lifetime of the
            # identifier
            self.backend.update_ttl(run_identifier, settings.CELERY_CONFIG
                                    .get('CELERY_TASK_RESULT_EXPIRES', 1800))

        if self.backend.get_set_cardinality(source_run_identifier) < 1 and run_result != 'running':
            # All tasks for a source (i.e. all meetings, committees etc.) have finished
            self.run_finished(**kwargs)

    def _remove_chain(self, run_identifier, value):
        self.backend.remove_value_from_set(run_identifier, value)

    def run_finished(self, run_identifier, **kwargs):
        raise NotImplementedError('Cleanup is highly dependent on what you use '
                                  'for storage, so this should be implemented '
                                  'in a subclass.')


class CleanupElasticsearch(BaseCleanup):
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=1, decode_responses=True)

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

        self.signal_processing_finished(**kwargs)

        return result

    """
    If a lock_key was passed, empty it to signal that next source may be processed.
    Only proceed if lock_key contains the current source.
    """
    def signal_processing_finished(self, **kwargs):
        source = kwargs['source_definition']['key']

        IndexedFile(kwargs.get('source_definition').get('indexed_filename')).signal_end(source)

        lock_key = kwargs.get('source_definition').get('lock_key')
        if lock_key is None:
            return
        lock_value = self.redis_client.get(lock_key)
        if lock_value is not None:
            _, _, lock_value = lock_value.split('.')

        if lock_value == source:
            log.info(f"[{source}] Finished, releasing the lock")
            self.redis_client.delete(lock_key)
        elif lock_value is not None:
            message = f"[{source}] the retrieved lock value is {lock_value}, different from source {source}, this should not happen"
            log.warning(message)
            raise Exception(message)
        else:
            message = f"[{source}] a lock_key was provided but the lock_value is None, this should not happen"
            log.warning(message)
            raise Exception(message)

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
