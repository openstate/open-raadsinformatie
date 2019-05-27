from ocd_backend import settings
from ocd_backend.es import elasticsearch
from ocd_backend.exceptions import ConfigurationError
from ocd_backend.log import get_source_logger
from ocd_backend.utils import json_encoder
from ocd_backend.utils.misc import get_sha1_hash
from ocd_backend.models.serializers import JsonLDSerializer
from ocd_backend.loaders import BaseLoader

log = get_source_logger('elasticsearch_loader')


class ElasticsearchLoader(BaseLoader):
    """Indexes items into Elasticsearch.

    Each item is added to two indexes: a 'combined' index that contains
    items from different sources, and an index that only contains items
    of the same source as the item.

    Each URL found in ``media_urls`` is added as a document to the
    ``RESOLVER_URL_INDEX`` (if it doesn't already exist).
    """

    def run(self, *args, **kwargs):
        self.index_name = kwargs.get('new_index_name')

        if not self.index_name:
            raise ConfigurationError('The name of the index is not provided')

        return super(ElasticsearchLoader, self).run(*args, **kwargs)

    def load_item(self, doc):
        # Recursively index associated models like attachments
        for model in doc.traverse():
            body = json_encoder.encode(JsonLDSerializer().serialize(model))

            log.debug('ElasticsearchLoader indexing document id: %s' % model.get_ori_identifier())

            # Index documents into new index
            elasticsearch.index(index=self.index_name, body=body, id=model.get_short_identifier())

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
                                    id=get_sha1_hash(model.original_url), body=url_doc)


class ElasticsearchUpdateOnlyLoader(ElasticsearchLoader):
    """
    Updates elasticsearch items using the update method. Use with caution.
    """

    def load_item(self, doc):
        body = json_encoder.encode(JsonLDSerializer().serialize(doc))

        if doc == {}:
            log.info('Empty document ....')
            return

        log.debug('ElasticsearchUpdateOnlyLoader indexing document id: %s' % doc.get_ori_identifier())

        # Index documents into new index
        elasticsearch.update(
            id=doc.get_short_identifier(),
            index=self.index_name,
            body={'doc': body},
        )
        # remember, resolver URLs are not update here to prevent too complex
        # things


class ElasticsearchUpsertLoader(ElasticsearchLoader):
    """
    Updates elasticsearch items using the update method. Use with caution.
    """

    def load_item(self, doc):
        body = json_encoder.encode(JsonLDSerializer().serialize(doc))

        if doc == {}:
            log.info('Empty document ....')
            return

        log.debug('ElasticsearchUpsertLoader indexing document id: %s' % doc.get_ori_identifier())

        # Index documents into new index
        elasticsearch.update(
            id=doc.get_short_identifier(),
            index=self.index_name,
            body={
                'doc': body,
                'doc_as_upsert': True,
            },
        )
