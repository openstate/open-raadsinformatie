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

    extractors = (
        source_definition.get('extractors', None) or
        [source_definition['extractor']])
    transformers = (
        source_definition.get('transformers', None) or
        [source_definition['transformer']])
    item_transformers = (
        source_definition.get('items', None) or
        [source_definition['item']])
    enrichers = [(load_object(enricher[0])(), enricher[1]) for enricher in
                 source_definition['enrichers']]
    loaders = (
        source_definition.get('loaders', None) or
        [source_definition['loader']])

    first_extractor = extractors.pop(0)
    try:
        for item in load_object(first_extractor)(source_definition).run():
            # FIXME: this currently requires that the number of transformers
            # and item transformers are the same. We should print an error if
            # not?
            for transformer, item_transformer in zip(
                transformers, item_transformers
            ):
                step_chain = chain()

                params['chain_id'] = uuid4().hex
                celery_app.backend.add_value_to_set(
                    set_name=run_identifier_chains,
                    value=params['chain_id'])

                # the item transformer is actually fired by the transformer
                # hence, we need to modify the source definition in place
                # to make sure it fires the item transformer we need ...
                transformer_source_definition = deepcopy(source_definition)
                transformer_source_definition['item'] = item_transformer

                # FIXME: Biggest problem with this step is that is does not
                # differentiate between first-step extractors and after ...
                for step in extractors:
                    step_class = load_object(step)(
                        transformer_source_definition)
                    step_chain |= step_class.s(*item, **params)

                # FIXME: current implementation for transformers + item
                # transformers causes multiple extraction rounds, which is
                # not what we want. Need to separate this step, if possible.
                step_class = load_object(transformer)()
                step_chain |= step_class.s(
                    *item, source_definition=transformer_source_definition,
                    **params)

                # Enrich
                for enricher_task, enricher_settings in enrichers:
                    step_chain |= enricher_task.s(
                        source_definition=transformer_source_definition,
                        enricher_settings=enricher_settings,
                        **params
                    )

                initialized_loaders = []
                for step in loaders:
                    step_class = load_object(step)()
                    initialized_loaders.append(step_class.s(
                        source_definition=transformer_source_definition,
                        **params))
                step_chain |= group(initialized_loaders)

                step_chain.delay()
    except:
        logger.error('An exception has occured in the "{extractor}" extractor.'
                     ' Setting status of run identifier "{run_identifier}" to '
                     '"error".'
                     .format(index=params['new_index_name'],
                             run_identifier=params['run_identifier'],
                             extractor=first_extractor))

        celery_app.backend.set(params['run_identifier'], 'error')
        raise

    celery_app.backend.set(params['run_identifier'], 'done')
