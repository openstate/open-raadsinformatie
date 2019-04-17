import json
from datetime import datetime

import requests

from ocd_backend import celery_app
from ocd_backend import settings
from ocd_backend.es import elasticsearch
from ocd_backend.exceptions import ConfigurationError
from ocd_backend.log import get_source_logger
from ocd_backend.mixins import (OCDBackendTaskSuccessMixin,
                                OCDBackendTaskFailureMixin)
from ocd_backend.utils import json_encoder
from ocd_backend.utils.misc import iterate, get_sha1_hash, doc_type
from ocd_backend.models.serializers import JsonLDSerializer, JsonSerializer

log = get_source_logger('loader')


class BaseLoader(OCDBackendTaskSuccessMixin, OCDBackendTaskFailureMixin,
                 celery_app.Task):
    """The base class that other loaders should inherit."""

    def run(self, *args, **kwargs):
        """Start loading of a single item.

        This method is called by the transformer and expects args to
        contain the output of the transformer as a tuple.
        Kwargs should contain the ``source_definition`` dict.

        :returns: the output of :py:meth:`~BaseTransformer.transform_item`
        """
        self.source_definition = kwargs['source_definition']

        for _, item in iterate(args):
            self.post_processing(item)
            self.load_item(item)

    def load_item(self, doc):
        raise NotImplementedError

    @staticmethod
    def post_processing(doc):
        # Add the 'processing.finished' datetime to the documents
        finished = datetime.now()
        # doc.Meta.processing_finished = finished


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
        body = json_encoder.encode(JsonLDSerializer().serialize(doc))

        log.info('ElasticsearchLoader indexing document id: %s' % doc.get_ori_identifier())

        # Index documents into new index
        elasticsearch.index(index=self.index_name, doc_type=doc_type(doc.verbose_name()),
                            body=body, id=doc.get_short_identifier())

        # Recursively index associated models like attachments
        for _, value in doc.properties(rels=True, props=False):
            self.load_item(value)

            if 'enricher_task' in value:
                # The value seems to be enriched so add to resolver
                url_doc = {
                    'ori_identifier': value.get_short_identifier(),
                    'original_url': value.original_url,
                    'file_name': value.name,
                }

                if 'content_type' in value:
                    url_doc['content_type'] = value.content_type

                # Update if already exists
                elasticsearch.index(index=settings.RESOLVER_URL_INDEX, doc_type='url',
                                    id=get_sha1_hash(value.original_url), body=url_doc)


class ElasticsearchUpdateOnlyLoader(ElasticsearchLoader):
    """
    Updates elasticsearch items using the update method. Use with caution.
    """

    def load_item(self, doc):
        body = json_encoder.encode(JsonLDSerializer().serialize(doc))

        if doc == {}:
            log.info('Empty document ....')
            return

        log.info('ElasticsearchUpdateOnlyLoader indexing document id: %s' % doc.get_ori_identifier())

        # Index documents into new index
        elasticsearch.update(
            id=doc.get_short_identifier(),
            index=self.index_name,
            doc_type=doc_type(doc.verbose_name()),
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

        log.info('ElasticsearchUpsertLoader indexing document id: %s' % doc.get_ori_identifier())

        # Index documents into new index
        elasticsearch.update(
            id=doc.get_short_identifier(),
            index=self.index_name,
            doc_type=doc_type(doc),
            body={
                'doc': body,
                'doc_as_upsert': True,
            },
        )


class DummyLoader(BaseLoader):
    """
    Prints the item to the console, for debugging purposes.
    """

    def load_item(self, doc):
        log.debug('=' * 50)
        log.debug('%s %s %s' % ('=' * 4, doc.get_ori_identifier(), '=' * 4))
        log.debug('%s %s %s' % ('-' * 20, 'doc', '-' * 25))
        log.debug(JsonSerializer().serialize(doc))
        log.debug('=' * 50)

    @staticmethod
    def run_finished(run_identifier):
        log.debug('*' * 50)
        log.debug('Finished run {}'.format(run_identifier))
        log.debug('*' * 50)


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")


class PopitLoader(BaseLoader):
    """
    Loads data to a Popit instance.
    """

    def _create_or_update_item(self, item, item_id):
        """
        First tries to post (aka create) a new item. If that does not work,
        do an update (aka put).
        """

        headers = {
            "Apikey": self.source_definition['popit_api_key'],
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        popit_url = "%s/%s" % (
            self.source_definition['popit_base_url'],
            self.source_definition['doc_type'],)
        resp = requests.post(
            popit_url,
            headers=headers, data=json.dumps(item, default=json_serial))

        # popit update controls where we should update the data from ibabs (overwriting our own data)
        # or whether we should only add things when there's new information.
        if (not self.source_definition.get('popit_update', False)) or (resp.status_code != 500):
            return resp

        return requests.put(
            "%s/%s" % (popit_url, item_id,),
            headers=headers, data=json.dumps(item, default=json_serial))

    def load_item(self, doc):
        resp = self._create_or_update_item(doc, doc.get_short_identifier())
