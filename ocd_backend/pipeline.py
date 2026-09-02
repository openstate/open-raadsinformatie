from copy import deepcopy
from datetime import datetime
from uuid import uuid4

import os

from celery import chain, group
from elasticsearch.exceptions import NotFoundError

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.es import elasticsearch as es
from ocd_backend.exceptions import ConfigurationError
from ocd_backend.hash_for_item import DUMMY_ITEM_HASH
from ocd_backend.log import get_source_logger
from ocd_backend.utils.pipeline_utils import PipelineUtils
from ocd_backend.utils.retry_utils import retry_task
from ocd_backend.utils.misc import load_object, propagate_chain_get
from ocd_backend.settings import LEAN_JUST_AGENDAS, RETRY_MAX_RETRIES

log = get_source_logger('pipeline')

@celery_app.task(bind=True, max_retries=RETRY_MAX_RETRIES)
@retry_task
def setup_pipeline(self, source_definition, source_run_uuid):
    log.debug(f'[{source_definition["key"]}] Starting pipeline for source: {source_definition.get("id")} with run uuid {source_run_uuid}')

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
        'source_run_identifier': 'pipeline_{}'.format(source_run_uuid),
        'run_identifier': 'pipeline_{}'.format(uuid4().hex),
        'current_index_name': current_index_name,
        'new_index_name': new_index_name,
        'index_alias': index_alias,
    }

    log.debug(f'[{source_definition["key"]}] Starting run with identifier {params["run_identifier"]}')

    celery_app.backend.set(params['run_identifier'], 'running')
    run_identifier_chains = '{}_chains'.format(params['run_identifier'])

    pipeline = source_definition

    if 'id' not in pipeline:
        raise ConfigurationError("Each pipeline must have an id field.")

    pipeline_definition = deepcopy(source_definition)
    pipeline_definition.update(pipeline)

    # initialize the ETL classes, per pipeline
    pipeline_extractor = load_object(
        pipeline_definition['extractor'])

    pipeline_transformer = load_object(
        pipeline_definition['transformer'])

    pipeline_enricher = [
        (load_object(enricher) or {}) for enricher in
        pipeline_definition.get('enrichers', [])]

    pipeline_loader = list()
    for cls in pipeline_definition.get('loaders', None) or \
            [pipeline_definition.get('loader', None)]:
        if cls:
            pipeline_loader.append(load_object(cls))

    pipeline_finalizer = load_object(
        pipeline_definition['finalizer'])


    result = None
    try:
        # The first extractor should be a generator instead of a task
        for item in pipeline_extractor(source_definition=pipeline_definition).run():
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

            celery_app.backend.add_value_to_set(
                set_name=params['source_run_identifier'],
                value=params['chain_id'])

            if hash_for_item != DUMMY_ITEM_HASH:
                # Transformers
                if pipeline_transformer:
                    step_chain.append(pipeline_transformer.s(
                        *item,
                        source_definition=pipeline_definition,
                        **params)
                    )

                # Enrichers
                for enricher_task in pipeline_enricher:
                    step_chain.append(enricher_task.s(
                        source_definition=pipeline_definition,
                        **params
                    )
                    )

            # Loaders
            # Multiple loaders to enable to save to different stores
            initialized_loaders = []
            for loader in pipeline_loader:
                initialized_loaders.append(loader.s(
                    source_definition=pipeline_definition,
                    **params))
            step_chain.append(group(initialized_loaders))

            # Finalizer
            if pipeline_finalizer and hash_for_item != DUMMY_ITEM_HASH:
                step_chain.append(pipeline_finalizer.s(
                    source_definition=pipeline_definition,
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

        blocked_from_api = source_definition.get('blocked_from_api')
        if not blocked_from_api:
            # Reraise the exception so celery can retry
            raise

    celery_app.backend.set(params['run_identifier'], 'done')
    log.info(f'[{source_definition["key"]}] Finished run with identifier {params["run_identifier"]}')

    if result and source_definition.get('wait_until_finished'):
        # Wait for last task chain to end before continuing
        log.info(f'[{source_definition["key"]}] Waiting for last chain to finish')
        propagate_chain_get(result)


@celery_app.task(bind=True)
def setup_synced_pipeline(self, sources, available_sources, lock_key, maintenance_file, settings, enabled_entities):
    log.debug(f'Starting synced pipeline for {len(sources)} sources')
    pipeline_utils = PipelineUtils()

    if pipeline_utils.is_maintenance(maintenance_file):
        log.info(f"...bailing out because maintenance file {maintenance_file} detected")
        return

    # Requeue if locked
    if pipeline_utils.is_locked(lock_key):
        log.debug("...sleeping/returning")
        if len(sources) > 0:
          setup_synced_pipeline.apply_async(args=[sources, available_sources, lock_key, maintenance_file, settings, enabled_entities], countdown=5)
        return

    source = sources.pop(0)
    pipeline_utils.claim_lock(lock_key, source)
    try:
        project, provider, source_name = source.split('.')
        available_source = available_sources['%s.%s' % (project, provider)][source_name]
        pipeline_utils.update_lock(lock_key, source, f"{project}.{provider}.{available_source['key']}")
        source_run_uuid = uuid4().hex

        log.info(f'[{source_name}] Start extract for {source_name}')

        selected_entities = []
        for entity in available_source.get('entities', []):
            if not enabled_entities or entity.get('entity') in enabled_entities:
                entity_name = entity.get('entity')
                if LEAN_JUST_AGENDAS and entity_name != 'meetings':
                    log.info(f'[{source_name}] Skipping entity {entity_name}, only interested in agenda')
                    continue
                selected_entities.append(entity_name)

                # Redis settings are overruled by source definitions, for some sources a start_date must be enforced
                new_source = deepcopy(settings)
                new_source.update(deepcopy(available_source))
                new_source.update(entity)

                setup_pipeline.delay(new_source, source_run_uuid)

        log.info(f'[{source_name}] Started pipelines: {", ".join(selected_entities)}')
        if len(sources) > 0:
          setup_synced_pipeline.apply_async(args=[sources, available_sources, lock_key, maintenance_file, settings, enabled_entities], countdown=5)
    except ValueError as e:
        log.error(f'Invalid source format {source} in redis')
        raise e
    except KeyError as e:
        log.error(f'Source {source} in redis does not exist in available sources')
        raise e
