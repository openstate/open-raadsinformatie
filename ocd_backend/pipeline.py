import os
import shutil
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
from ocd_backend.utils.misc import load_object, propagate_chain_get

logger = get_source_logger('pipeline')


@celery_app.task(autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def setup_pipeline(source_definition):
    logger.debug('[%s] Starting pipeline for source: %s' % (source_definition['key'], source_definition.get('id')))

    # index_name is an alias of the current version of the index
    index_alias = '{prefix}_{index_name}'.format(
        prefix=source_definition.get('es_prefix', settings.DEFAULT_INDEX_PREFIX),
        index_name=source_definition.get('index_name',
                                         source_definition.get('id'))
    )

    # Purge and recreate temp dir to prevent No space left on device, see #236
    try:
        shutil.rmtree(settings.TEMP_DIR_PATH, ignore_errors=True)
        os.mkdir(settings.TEMP_DIR_PATH)
    except OSError:
        pass

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

    current_index_name = current_index_aliases.keys()[0]
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
        'index_alias': index_alias
    }

    logger.debug('[%s] Starting run with identifier %s' % (source_definition['key'], params['run_identifier']))

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

    result = None
    for pipeline in pipelines:
        try:
            # The first extractor should be a generator instead of a task
            for item in pipeline_extractors[pipeline['id']](
                    source_definition=pipeline_definitions[pipeline['id']]).run():

                step_chain = list()

                params['chain_id'] = uuid4().hex
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

                result = chain(step_chain).delay()
        except KeyboardInterrupt:
            logger.warning('KeyboardInterrupt received. Stopping the program.')
            exit()
        except Exception, e:
            logger.error('[{site_name}] Pipeline has failed. Setting status of '
                         'run identifier "{run_identifier}" to "error":\n{message}'
                         .format(index=params['new_index_name'],
                                 run_identifier=params['run_identifier'],
                                 extractor=pipeline_extractors[pipeline['id']],
                                 message=e,
                                 site_name=source_definition['key'],
                                 )
                         )

            celery_app.backend.set(params['run_identifier'], 'error')

            # Reraise the exception so celery can autoretry
            raise

    celery_app.backend.set(params['run_identifier'], 'done')
    logger.info("[%s] Finished run with identifier %s" % (source_definition['key'], params['run_identifier']))

    if result and source_definition.get('wait_until_finished'):
        # Wait for last task chain to end before continuing
        logger.info("[%s] Waiting for last chain to finish" % source_definition['key'])
        propagate_chain_get(result)
