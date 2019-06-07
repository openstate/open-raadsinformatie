from ocd_backend import celery_app
from ocd_backend import settings
from ocd_backend.es import elasticsearch as es
from ocd_backend.log import get_source_logger

log = get_source_logger('ocd_backend.tasks')


class BaseCleanup(celery_app.Task):
    ignore_result = True

    def start(self, *args, **kwargs):
        run_identifier = kwargs.get('run_identifier')
        run_identifier_chains = '{}_chains'.format(run_identifier)
        self._remove_chain(run_identifier_chains, kwargs.get('chain_id'))

        if self.backend.get_set_cardinality(run_identifier_chains) < 1 and self.backend.get(run_identifier) == 'done':
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
        log.info('Finished run {}.'.format(run_identifier))


@celery_app.task(bind=True, base=CleanupElasticsearch, autoretry_for=(Exception,), retry_backoff=True)
def cleanup_elasticsearch(self, *args, **kwargs):
    return self.start(*args, **kwargs)


@celery_app.task(bind=True, base=DummyCleanup, autoretry_for=(Exception,), retry_backoff=True)
def dummy_cleanup(self, *args, **kwargs):
    return self.start(*args, **kwargs)
