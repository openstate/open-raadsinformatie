from elasticsearch import Elasticsearch
from time import sleep
import json

from ocd_backend.extractors import BaseExtractor, HttpRequestMixin
from ocd_backend.extractors import log
from ocd_backend.exceptions import NotFound
from ocd_backend.settings import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT


class MetadataExtractor(BaseExtractor, HttpRequestMixin):
    metadata_base_url = 'http://e.omroep.nl/metadata/'

    def call(self, url):
        url = '%s%s' % (self.metadata_base_url, url)
        log.debug('Getting %s' % (url))
        r = self.http_session.get(url)
        r.raise_for_status()
        return r.text

    def get_items(self, es, index, field):
        scroll = es.search(
            index=index,
            scroll='5m',
            search_type='scan',
            fields=field
        )
        scroll_id = scroll['_scroll_id']
        items_left = scroll['hits']['total']

        items = []
        while items_left > 0:
            results = es.scroll(scroll_id=scroll_id, scroll='5m')
            items_left -= len(results['hits']['hits'])
            for hit in results['hits']['hits']:
                if 'fields' not in hit:
                    continue
                items.append(hit['fields'][field][0])

        return set(items)

    def get_metadata(self):
        # Retrieve the PRIDs from the PRID index. This assumes that the
        # PRID source has already been extracted.
        es = Elasticsearch(
            hosts='%s:%s' % (ELASTICSEARCH_HOST, ELASTICSEARCH_PORT)
        )

        prids = self.get_items(es, 'npo_prid', 'prid')
        metadata_prids = self.get_items(es, 'npo_metadata', 'prid')

        new_prids = prids - metadata_prids

        len_prids = len(new_prids)
        for idx, PRID in enumerate(new_prids):
            print 'Downloading PRID %s/%s: %s' % (idx + 1, len_prids, PRID)
            metadata = self.call(PRID)
            # Remove the function call 'parseMetadata(' and its
            # closing parenthesis which are always part of the
            # metadata
            metadata = metadata.split("\n")[0][14:-1]
            try:
                metadata_json = json.loads(metadata)
            except ValueError, e:
                print 'Invalid metadata JSON: ' + str(e)
                continue
            yield metadata_json

    def run(self):
        for item in self.get_metadata():
            yield 'application/json', json.dumps(item)
