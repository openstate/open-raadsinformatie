import json

from ocd_backend import celery_app
from ocd_backend import settings
from ocd_backend.es import elasticsearch
from ocd_backend.exceptions import ConfigurationError
from ocd_backend.loaders import BaseLoader
from ocd_backend.log import get_source_logger
from ocd_backend.models.serializers import JsonLDSerializer
from ocd_backend.utils import json_encoder
from ocd_backend.utils.misc import get_sha1_hash

log = get_source_logger('elasticsearch_loader')


class ElasticsearchLoader(BaseLoader):
    """Indexes items into Elasticsearch.

    Each URL found in ``media_urls`` is added as a document to the
    ``RESOLVER_URL_INDEX`` (if it doesn't already exist).
    """

    def start(self, *args, **kwargs):
        self.index_name = kwargs.get('new_index_name')

        if not self.index_name:
            raise ConfigurationError('The name of the index is not provided')

        return super(ElasticsearchLoader, self).start(*args, **kwargs)

    def load_item(self, doc):
        # Recursively index associated models like attachments
        for model in doc.traverse():
            model_body = json_encoder.encode(JsonLDSerializer(loader_class=self).serialize(model))

            log.debug('ElasticsearchLoader indexing document id: %s' % model.get_ori_identifier())

            # Index document into new index
            elasticsearch.index(index=self.index_name,
                                body=model_body,
                                id=model.get_short_identifier())

            if 'enricher_task' in model:
                # The value seems to be enriched so add to resolver
                url_doc = {
                    'ori_identifier': model.get_short_identifier(),
                    'original_url': model.original_url,
                    'file_name': model.name,
                }

                if 'content_type' in model:
                    url_doc['content_type'] = model.content_type

                # Update if already exists
                elasticsearch.index(index=settings.RESOLVER_URL_INDEX,
                                    id=get_sha1_hash(model.original_url),
                                    body=url_doc)


class ElasticsearchUpdateOnlyLoader(ElasticsearchLoader):
    """
    Updates elasticsearch items using the update method. Use with caution.
    """

    def load_item(self, doc):
        # Recursively index associated models like attachments
        for model in doc.traverse():
            model_body = json_encoder.encode(JsonLDSerializer(loader_class=self).serialize(model))

            if doc == {}:
                log.info('Empty document ....')
                return

            log.debug('ElasticsearchUpdateOnlyLoader indexing document id: %s' % model.get_ori_identifier())

            # Index document into new index
            elasticsearch.update(
                id=model.get_short_identifier(),
                index=self.index_name,
                body={'doc': json.loads(model_body)},
            )

            # Resolver URLs are not updated here to prevent too complex things


class ElasticsearchUpsertLoader(ElasticsearchLoader):
    """
    Updates elasticsearch items using the update method.
    """

    def load_item(self, doc):
        # Recursively index associated models like attachments
        for model in doc.traverse():
            model_body = json_encoder.encode(JsonLDSerializer(loader_class=self).serialize(model))

            log.debug('ElasticsearchUpsertLoader indexing document id: %s' % model.get_ori_identifier())

            # Update document
            elasticsearch.update(
                id=model.get_short_identifier(),
                index=self.index_name,
                body={'doc': json.loads(model_body),
                      'doc_as_upsert': True,
                },
            )

            if 'enricher_task' in model:
                # The value seems to be enriched so add to resolver
                url_doc = {
                    'ori_identifier': model.get_short_identifier(),
                    'original_url': model.original_url,
                    'file_name': model.name,
                }

                if 'content_type' in model:
                    url_doc['content_type'] = model.content_type

                # Update if already exists
                elasticsearch.index(index=settings.RESOLVER_URL_INDEX,
                                    id=get_sha1_hash(model.original_url),
                                    body=url_doc)


@celery_app.task(bind=True, base=ElasticsearchLoader, autoretry_for=(Exception,), retry_backoff=True)
def elasticsearch_loader(self, *args, **kwargs):
    return self.start(*args, **kwargs)


@celery_app.task(bind=True, base=ElasticsearchUpdateOnlyLoader, autoretry_for=(Exception,), retry_backoff=True)
def elasticsearch_update_only_loader(self, *args, **kwargs):
    return self.start(*args, **kwargs)


@celery_app.task(bind=True, base=ElasticsearchUpsertLoader, autoretry_for=(Exception,), retry_backoff=True)
def elasticsearch_upsert_loader(self, *args, **kwargs):
    return self.start(*args, **kwargs)
