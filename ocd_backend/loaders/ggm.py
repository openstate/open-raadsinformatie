import json

from ocd_backend.loaders import BaseLoader
from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.exceptions import ConfigurationError
from ocd_backend.utils.misc import json_datetime

from elasticsearch import ConflictError
from ocd_backend import settings
from ocd_backend.es import elasticsearch
from ocd_backend.log import get_source_logger

log = get_source_logger('loader')


class GegevensmagazijnElasticsearchLoader(BaseLoader):

    def run(self, args, **kwargs):
        self.source_definition = kwargs['source_definition']

        self.current_index_name = kwargs.get('current_index_name')
        self.index_name = kwargs.get('new_index_name')
        self.alias = kwargs.get('index_alias')

        if not self.index_name:
            raise ConfigurationError('The name of the index is not provided')

        for arg in args:
            self.doc_type = arg[-1]
            super(GegevensmagazijnElasticsearchLoader, self).run(arg[:-1], **kwargs)
        return True

    def load_item(
        self, combined_object_id, object_id, combined_index_doc, doc
    ):
        log.info('Indexing document id: %s' % object_id)
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


class GegevensmagazijnLDPLoader(BaseLoader, HttpRequestMixin):

    def run(self, args, **kwargs):
        self.source_definition = kwargs['source_definition']

        for arg in args:
            self.doc_type = arg[-1]
            super(GegevensmagazijnLDPLoader, self).run(arg[:-1], **kwargs)

    def load_item(self, combined_object_id, object_id, combined_index_doc, doc):
        data = json.dumps(doc, default=json_datetime)
        self.http_session.headers['Content-Type'] = 'application/json'
        self.http_session.headers['Link'] = '<http://json-ld.org/contexts/%s.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"' % self.doc_type
        #print self.http_session.post(ldp_loader_url, data=data)
