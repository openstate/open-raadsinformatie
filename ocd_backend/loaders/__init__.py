from datetime import datetime

from elasticsearch import ConflictError
from ocd_backend import celery_app

from ocd_backend import settings
from ocd_backend.es import elasticsearch
from ocd_backend.exceptions import ConfigurationError
from ocd_backend.log import get_source_logger
from ocd_backend.mixins import (OCDBackendTaskSuccessMixin,
                                OCDBackendTaskFailureMixin)

log = get_source_logger('loader')


class BaseLoader(OCDBackendTaskSuccessMixin, OCDBackendTaskFailureMixin,
                 celery_app.Task):
    """The base class that other loaders should inherit."""

    def run(self, *args, **kwargs):
        """Start loading of a single item.

        This method is called by the transformer and expects args to
        contain the output of the transformer as a tuple.
        Kwargs should contain the ``source_definition`` dict.

        :param item:
        :param source_definition: The configuration of a single source in
            the form of a dictionary (as defined in the settings).
        :type source_definition: dict.
        :returns: the output of :py:meth:`~BaseTransformer.transform_item`
        """
        self.source_definition = kwargs['source_definition']

        combined_object_id, object_id, combined_index_doc, doc = args[0]

        # Add the 'processing.finished' datetime to the documents
        finished = datetime.now()
        combined_index_doc['meta']['processing_finished'] = finished
        doc['meta']['processing_finished'] = finished

        return self.load_item(combined_object_id, object_id,
                              combined_index_doc, doc)

    def load_item(
        self, combined_object_id, object_id, combined_index_doc, doc
    ):
        raise NotImplemented


class ElasticsearchLoader(BaseLoader):
    """Indexes items into Elasticsearch.

    Each item is added to two indexes: a 'combined' index that contains
    items from different sources, and an index that only contains items
    of the same source as the item.

    Each URL found in ``media_urls`` is added as a document to the
    ``RESOLVER_URL_INDEX`` (if it doesn't already exist).
    """
    def run(self, *args, **kwargs):
        self.current_index_name = kwargs.get('current_index_name')
        self.index_name = kwargs.get('new_index_name')
        self.alias = kwargs.get('index_alias')
        self.doc_type = kwargs['source_definition'].get('doc_type', 'item')

        if not self.index_name:
            raise ConfigurationError('The name of the index is not provided')

        return super(ElasticsearchLoader, self).run(*args, **kwargs)

    def load_item(
        self, combined_object_id, object_id, combined_index_doc, doc
    ):
        log.info('Indexing documents...')
        elasticsearch.index(index=settings.COMBINED_INDEX,
                            doc_type=self.doc_type, id=combined_object_id,
                            body=combined_index_doc)

        # Index documents into new index
        elasticsearch.index(index=self.index_name, doc_type=self.doc_type,
                            body=doc, id=object_id)

        m_url_content_types = {}
        if 'media_urls' in doc['enrichments']:
            for media_url in doc['enrichments']['media_urls']:
                if 'content_type' in media_url:
                    m_url_content_types[media_url['original_url']] = \
                        media_url['content_type']

        # For each media_urls.url, add a resolver document to the
        # RESOLVER_URL_INDEX
        if 'media_urls' in doc:
            for media_url in doc['media_urls']:
                url_hash = media_url['url'].split('/')[-1]
                url_doc = {
                    'original_url': media_url['original_url']
                }

                if media_url['original_url'] in m_url_content_types:
                    url_doc['content_type'] = \
                        m_url_content_types[media_url['original_url']]

                try:
                    elasticsearch.create(index=settings.RESOLVER_URL_INDEX,
                                         doc_type='url', id=url_hash,
                                         body=url_doc)
                except ConflictError:
                    log.debug('Resolver document %s already exists' % url_hash)


class DummyLoader(BaseLoader):
    """
    Prints the item to the console, for debugging purposes.
    """
    def load_item(
        self, combined_object_id, object_id, combined_index_doc, doc,
        transformer_task_id
    ):
        print '=' * 50
        print '%s %s %s' % ('=' * 4, combined_object_id, '=' * 4)
        print '%s %s %s' % ('=' * 4, object_id, '=' * 4)
        print '%s %s %s' % ('-' * 20, 'combined', '-' * 20)
        print combined_index_doc
        print '%s %s %s' % ('-' * 20, 'doc', '-' * 25)
        print doc
        print '=' * 50

    def run_finished(self, run_identifier):
        print '*' * 50
        print
        print 'Finished run {}'.format(run_identifier)
        print
        print '*' * 50
