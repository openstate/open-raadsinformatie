from datetime import datetime
from uuid import uuid4
from copy import deepcopy

from elasticsearch.exceptions import NotFoundError
from celery import chain, group

from ocd_backend.es import elasticsearch as es
from ocd_backend import settings, celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.utils.misc import load_object, propagate_chain_get
from ocd_backend.exceptions import ConfigurationError

logger = get_source_logger('pipeline')


def setup_pipeline(source_definition):
    logger.info('Starting pipeline for source: %s' % source_definition.get('id'))

    # index_name is an alias of the current version of the index
    index_alias = '{prefix}_{index_name}'.format(
        prefix=settings.DEFAULT_INDEX_PREFIX,
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

    celery_app.backend.set(params['run_identifier'], 'running')
    run_identifier_chains = '{}_chains'.format(params['run_identifier'])

    # we can have multiple pipelines. but for compatibility and readability
    # use the source definition if no specific pipelines have been defined
    pipelines = source_definition.get('pipelines', None) or [source_definition]

    pipeline_definitions = {}
    pipeline_extractors = {}
    pipeline_extensions = {}
    pipeline_transformers = {}
    pipeline_enrichers = {}
    pipeline_loaders = {}

    for pipeline in pipelines:
        if 'id' not in pipeline:
            raise ConfigurationError("Each pipeline must have an id field.")

        # adjusted source definitionsv per pipeline. This way you can for
        # example change the index on a pipeline basis
        pipeline_definitions[pipeline['id']] = deepcopy(source_definition)
        pipeline_definitions[pipeline['id']].update(pipeline)

        # initialize the ETL classes, per pipeline
        pipeline_extractors[pipeline['id']] = load_object(
            pipeline_definitions[pipeline['id']]['extractor'])

        pipeline_extensions[pipeline['id']] = [
            load_object(cls) for cls in
            pipeline_definitions[pipeline['id']].get('extensions', [])]

        pipeline_transformers[pipeline['id']] = load_object(
            pipeline['transformer'])()

        pipeline_enrichers[pipeline['id']] = [
            (load_object(enricher[0])(), enricher[1] or {}) for enricher in
            pipeline_definitions[pipeline['id']].get('enrichers', [])]

        pipeline_loaders[pipeline['id']] = [
            load_object(cls)() for cls in
            pipeline_definitions[pipeline['id']].get('loaders', None) or [
                pipeline_definitions[pipeline['id']]['loader']
            ]
        ]

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

                # Remaining extractors
                for extension in pipeline_extensions[pipeline['id']]:
                    step_chain.append(extension().s(
                        *item,
                        source_definition=pipeline_definitions[pipeline['id']],
                        **params
                        )
                    )
                    # Prevent old item being passed down to next steps
                    item = []

                # Transformers
                step_chain.append(pipeline_transformers[pipeline['id']].s(
                    *item,
                    source_definition=pipeline_definitions[pipeline['id']],
                    **params))

                # Enrichers
                for enricher_task, enricher_settings in pipeline_enrichers[
                    pipeline['id']
                ]:
                    step_chain.append(enricher_task.s(
                        source_definition=pipeline_definitions[
                            pipeline['id']],
                        enricher_settings=enricher_settings,
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
            logger.warn('KeyboardInterrupt received. Stopping the program.')
            exit()
        except Exception, e:
            logger.error('An exception has occured in the "{extractor}" extractor.'
                         ' Setting status of run identifier "{run_identifier}" to '
                         '"error":\n{message}'
                         .format(index=params['new_index_name'],
                                 run_identifier=params['run_identifier'],
                                 extractor=pipeline_extractors[pipeline['id']],
                                 message=e,
                                 )
                         )

            celery_app.backend.set(params['run_identifier'], 'error')
            raise

    celery_app.backend.set(params['run_identifier'], 'done')
    if result and source_definition.get('wait_until_finished'):
        # Wait for last task chain to end before continuing
        logger.debug("Waiting for last chain to finish")
        propagate_chain_get(result)

    print
