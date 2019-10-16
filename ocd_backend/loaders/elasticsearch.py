import simplejson as json

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.es import elasticsearch
from ocd_backend.exceptions import ConfigurationError
from ocd_backend.loaders import BaseLoader
from ocd_backend.log import get_source_logger
from ocd_backend.models.serializers import JsonLDSerializer
from ocd_backend.utils.misc import json_encoder, get_sha1_hash

log = get_source_logger('elasticsearch_loader')


class ElasticsearchLoader(BaseLoader):
    """Indexes items into Elasticsearch."""

    def start(self, *args, **kwargs):
        self.index_name = kwargs.get('new_index_name')

        if not self.index_name:
            raise ConfigurationError('The name of the index is not provided')

        return super(ElasticsearchLoader, self).start(*args, **kwargs)

    def load_item(self, doc):
        log_identifiers = []

        # Recursively index associated models like attachments
        for model in doc.traverse():
            model_body = json_encoder.encode(JsonLDSerializer(loader_class=self).serialize(model))

            # Index document into new index
            elasticsearch.index(index=self.index_name,
                                body=model_body,
                                id=model.get_short_identifier())

            log_identifiers.append(model.get_short_identifier())

        log.debug('ElasticsearchLoader indexing document id: %s' % ', '.join(log_identifiers))


class ElasticsearchUpdateOnlyLoader(ElasticsearchLoader):
    """
    Updates elasticsearch items using the update method. Use with caution.
    """

    def load_item(self, doc):
        log_identifiers = []

        # Recursively index associated models like attachments
        for model in doc.traverse():
            model_body = json_encoder.encode(JsonLDSerializer(loader_class=self).serialize(model))

            if doc == {}:
                log.info('Empty document ....')
                return

            # Index document into new index
            elasticsearch.update(
                id=model.get_short_identifier(),
                index=self.index_name,
                body={'doc': json.loads(model_body)},
            )

            log_identifiers.append(model.get_short_identifier())

            # Resolver URLs are not updated here to prevent too complex things

        log.debug('ElasticsearchUpdateOnlyLoader indexing document ids: %s' % ', '.join(log_identifiers))


class ElasticsearchUpsertLoader(ElasticsearchLoader):
    """
    Updates elasticsearch items using the update method.
    """

    def load_item(self, doc):
        log_identifiers = []

        # Recursively index associated models like attachments
        for model in doc.traverse():
            model_body = json_encoder.encode(JsonLDSerializer(loader_class=self).serialize(model))

            # Update document
            elasticsearch.update(
                id=model.get_short_identifier(),
                index=self.index_name,
                body={
                    'doc': json.loads(model_body),
                    'doc_as_upsert': True,
                },
            )

            log_identifiers.append(model.get_short_identifier())

        log.debug('ElasticsearchUpsertLoader indexing document ids: %s' % ', '.join(log_identifiers))


@celery_app.task(bind=True, base=ElasticsearchLoader, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def elasticsearch_loader(self, *args, **kwargs):
    return self.start(*args, **kwargs)


@celery_app.task(bind=True, base=ElasticsearchUpdateOnlyLoader, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def elasticsearch_update_only_loader(self, *args, **kwargs):
    return self.start(*args, **kwargs)


@celery_app.task(bind=True, base=ElasticsearchUpsertLoader, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def elasticsearch_upsert_loader(self, *args, **kwargs):
    return self.start(*args, **kwargs)
