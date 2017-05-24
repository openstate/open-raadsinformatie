from datetime import datetime
from uuid import uuid4
from copy import deepcopy

from elasticsearch.exceptions import NotFoundError
from celery import chain, group

from ocd_backend.es import elasticsearch as es
from ocd_backend import settings, celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.utils.misc import load_object
from ocd_backend.exceptions import ConfigurationError

logger = get_source_logger('pipeline')


def setup_pipeline(source_definition):
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
    if source_definition['keep_index_on_update']:
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
    extractors = list(set([p['extractor'] for p in pipelines]))

    pipeline_definitions = {}
    pipeline_transformers = {}
    pipeline_enrichers = {}
    pipeline_loaders = {}
    for pipeline in pipelines:
        # adjusted source definitionsv per pipeline. This way you can for
        # example change the index on a pipeline basis
        pipeline_definitions[pipeline['id']] = deepcopy(source_definition)
        pipeline_definitions[pipeline['id']].update(pipeline)

        # initialize the ETL classes, per pipeline
        pipeline_transformers[pipeline['id']] = load_object(
            pipeline['transformer'])()
        pipeline_enrichers[pipeline['id']] = [
            (load_object(enricher[0])(), enricher[1]) for enricher in
            pipeline_definitions[pipeline['id']]['enrichers']]
        pipeline_normalized_loaders = (
            pipeline_definitions[pipeline['id']].get('loaders', None) or
            [pipeline_definitions[pipeline['id']]['loader']])
        pipeline_loaders[pipeline['id']] = [
            load_object(pll)() for pll in pipeline_normalized_loaders]

    try:
        for extractor in extractors:
            for item in load_object(extractor)(source_definition).run():
                for pipeline in pipelines:
                    # skip if the extractor from the pipeline was different
                    # from the one we're extracting from right now
                    if pipeline['extractor'] != extractor:
                        continue

                    step_chain = chain()

                    params['chain_id'] = uuid4().hex
                    celery_app.backend.add_value_to_set(
                        set_name=run_identifier_chains,
                        value=params['chain_id'])

                    step_chain |= pipeline_transformers[pipeline['id']].s(
                        *item,
                        source_definition=pipeline_definitions[pipeline['id']],
                        **params)

                    # Enrich
                    for enricher_task, enricher_settings in pipeline_enrichers[
                        pipeline['id']
                    ]:
                        step_chain |= enricher_task.s(
                            source_definition=pipeline_definitions[
                                pipeline['id']],
                            enricher_settings=enricher_settings,
                            **params
                        )

                    # multiple loaders to enable to save to different stores
                    initialized_loaders = []
                    for loader in pipeline_loaders[pipeline['id']]:
                        initialized_loaders.append(loader.s(
                            source_definition=pipeline_definitions[
                                pipeline['id']],
                            **params))
                    step_chain |= group(initialized_loaders)

                    step_chain.delay()
    except:
        logger.error('An exception has occured in the "{extractor}" extractor.'
                     ' Setting status of run identifier "{run_identifier}" to '
                     '"error".'
                     .format(index=params['new_index_name'],
                             run_identifier=params['run_identifier'],
                             extractor=extractor))

        celery_app.backend.set(params['run_identifier'], 'error')
        raise

    celery_app.backend.set(params['run_identifier'], 'done')
