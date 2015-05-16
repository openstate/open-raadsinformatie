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

    def get_metadata(self):
        # Retrieve the PRIDs from the PRID index. This assumes that the
        # PRID source has already been extracted.
        es = Elasticsearch(
            hosts='%s:%s' % (ELASTICSEARCH_HOST, ELASTICSEARCH_PORT)
        )
        #TODO change ocd_prid name once ocd is removed from index names
        scroll = es.search(
            index='ocd_prid',
            scroll='5m',
            search_type='scan',
            fields='PRID'
        )

        scroll_id = scroll['_scroll_id']
        items_left = scroll['hits']['total']

        while items_left > 0:
            results = es.scroll(scroll_id=scroll_id, scroll='5m')
            items_left -= len(results['hits']['hits'])
            for hit in results['hits']['hits']:
                PRID = hit['fields']['PRID'][0]
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
