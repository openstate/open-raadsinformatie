from copy import deepcopy
from datetime import datetime
from uuid import uuid4

from celery import chain, group
from elasticsearch.exceptions import NotFoundError

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.es import elasticsearch as es
from ocd_backend.exceptions import ConfigurationError
from ocd_backend.log import get_source_logger
from ocd_backend.utils.retry_utils import retry_task
from ocd_backend.utils.misc import load_object, propagate_chain_get
from ocd_backend.settings import RETRY_MAX_RETRIES

log = get_source_logger('pipeline')

@celery_app.task(bind=True, max_retries=RETRY_MAX_RETRIES)
@retry_task
def setup_pipeline(self, source_definition):
    log.debug(f'[{source_definition["key"]}] Starting pipeline for source: {source_definition.get("id")}')

    # index_name is an alias of the current version of the index
    index_alias = '{prefix}_{index_name}'.format(
        prefix=source_definition.get('es_prefix', settings.DEFAULT_INDEX_PREFIX),
        index_name=source_definition.get('index_name',
                                         source_definition.get('id'))
    )

    if not es.indices.exists(index_alias):
        index_name = '{index_alias}_{now}'.format(index_alias=index_alias,
                                                  now=datetime.utcnow()
                                                  .strftime('%Y%m%d%H%M%S'))

        es.indices.create(index_name)
        es.indices.put_alias(name=index_alias, index=index_name)

    # Find the current index name behind the alias specified in the config
    try:
        current_index_aliases = es.indices.get_alias(name=index_alias)
    except NotFoundError:
        raise ConfigurationError('Index with alias "{index_alias}" does '
                                 'not exist'.format(index_alias=index_alias))

    current_index_name = list(current_index_aliases)[0]
    # Check if the source specifies that any update should be added to
    # the current index instead of a new one
    if source_definition.get('keep_index_on_update'):
        new_index_name = current_index_name
    else:
        new_index_name = '{index_alias}_{now}'.format(
            index_alias=index_alias,
            now=datetime.utcnow().strftime('%Y%m%d%H%M%S')
        )

    # Parameters that are passed to each task in the chain
    params = {
        'run_identifier': 'pipeline_{}'.format(uuid4().hex),
        'current_index_name': current_index_name,
        'new_index_name': new_index_name,
        'index_alias': index_alias,
    }

    log.debug(f'[{source_definition["key"]}] Starting run with identifier {params["run_identifier"]}')

    celery_app.backend.set(params['run_identifier'], 'running')
    run_identifier_chains = '{}_chains'.format(params['run_identifier'])

    # we can have multiple pipelines. but for compatibility and readability
    # use the source definition if no specific pipelines have been defined
    pipelines = source_definition.get('pipelines', None) or [source_definition]

    pipeline_definitions = {}
    pipeline_extractors = {}
    pipeline_transformers = {}
    pipeline_enrichers = {}
    pipeline_loaders = {}
    pipeline_finalizers = {}

    for pipeline in pipelines:
        if 'id' not in pipeline:
            raise ConfigurationError("Each pipeline must have an id field.")

        # adjusted source definitions per pipeline. This way you can for
        # example change the index on a pipeline basis
        pipeline_definitions[pipeline['id']] = deepcopy(source_definition)
        pipeline_definitions[pipeline['id']].update(pipeline)

        # initialize the ETL classes, per pipeline
        pipeline_extractors[pipeline['id']] = load_object(
            pipeline_definitions[pipeline['id']]['extractor'])

        pipeline_transformers[pipeline['id']] = load_object(
            pipeline_definitions[pipeline['id']]['transformer'])

        pipeline_enrichers[pipeline['id']] = [
            (load_object(enricher) or {}) for enricher in
            pipeline_definitions[pipeline['id']].get('enrichers', [])]

        pipeline_loaders[pipeline['id']] = list()
        for cls in pipeline_definitions[pipeline['id']].get('loaders', None) or \
                [pipeline_definitions[pipeline['id']].get('loader', None)]:
            if cls:
                pipeline_loaders[pipeline['id']].append(load_object(cls))

        pipeline_finalizers[pipeline['id']] = load_object(
            pipeline_definitions[pipeline['id']]['finalizer'])

    result = None
    for pipeline in pipelines:
        try:
            # The first extractor should be a generator instead of a task
            for item in pipeline_extractors[pipeline['id']](
                    source_definition=pipeline_definitions[pipeline['id']]).run():
                if len(item) == 5:
                    hash_for_item = item[-1]
                    item = item[:-1]
                else:
                    hash_for_item = None
                step_chain = list()

                params['chain_id'] = uuid4().hex
                params['start_time'] = datetime.now()

                celery_app.backend.add_value_to_set(
                    set_name=run_identifier_chains,
                    value=params['chain_id'])

                # Transformers
                if pipeline_transformers.get(pipeline['id']):
                    step_chain.append(pipeline_transformers[pipeline['id']].s(
                        *item,
                        source_definition=pipeline_definitions[pipeline['id']],
                        **params)
                    )

                # Enrichers
                for enricher_task in pipeline_enrichers[
                    pipeline['id']
                ]:
                    step_chain.append(enricher_task.s(
                        source_definition=pipeline_definitions[
                            pipeline['id']],
                        **params
                    )
                    )

                # Loaders
                # Multiple loaders to enable to save to different stores
                initialized_loaders = []
                for loader in pipeline_loaders[pipeline['id']]:
                    initialized_loaders.append(loader.s(
                        source_definition=pipeline_definitions[
                            pipeline['id']],
                        **params))
                step_chain.append(group(initialized_loaders))

                # Finalizer
                if pipeline_finalizers.get(pipeline['id']):
                    step_chain.append(pipeline_finalizers[pipeline['id']].s(
                        source_definition=pipeline_definitions[pipeline['id']],
                        hash_for_item=hash_for_item,
                        **params)
                    )

                result = chain(step_chain).delay()
        except KeyboardInterrupt:
            log.warning('KeyboardInterrupt received. Stopping the program.')
            exit()
        except Exception as e:
            log.info(f'[{source_definition["key"]}] Pipeline has failed. Setting status of run identifier '
                      f'{params["run_identifier"]} to "error" ({e.__class__.__name__}):\n{str(e)}')

            celery_app.backend.set(params['run_identifier'], 'error')

            # Reraise the exception so celery can retry
            raise

    celery_app.backend.set(params['run_identifier'], 'done')
    log.info(f'[{source_definition["key"]}] Finished run with identifier {params["run_identifier"]}')

    if result and source_definition.get('wait_until_finished'):
        # Wait for last task chain to end before continuing
        log.info(f'[{source_definition["key"]}] Waiting for last chain to finish')
        propagate_chain_get(result)
