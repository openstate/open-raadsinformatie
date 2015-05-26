from elasticsearch import Elasticsearch
from time import sleep
import json

from ocd_backend.extractors import BaseExtractor, HttpRequestMixin
from ocd_backend.extractors import log
from ocd_backend.exceptions import NotFound
from ocd_backend.settings import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT


class TT888Extractor(BaseExtractor, HttpRequestMixin):
    tt888_base_url = 'http://e.omroep.nl/tt888/'

    def call(self, url):
        url = '%s%s' % (self.tt888_base_url, url)
        log.debug('Getting %s' % (url))
        r = self.http_session.get(url)
        r.raise_for_status()
        return r.text

    def get_subtitles(self):
        # Retrieve the PRIDs from the PRID index. This assumes that the
        # PRID source has already been extracted.
        es = Elasticsearch(
            hosts='%s:%s' % (ELASTICSEARCH_HOST, ELASTICSEARCH_PORT)
        )
        scroll = es.search(
            index='npo_prid',
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
                subtitle = self.call(PRID)
                # Skip items which don't have subtitles
                if (subtitle.startswith('<')
                        or subtitle.startswith('No subtitle')):
                    continue
                tt888 = {
                    'prid': PRID,
                    'subtitle': subtitle
                }
                yield tt888

    def run(self):
        for item in self.get_subtitles():
            yield 'application/json', json.dumps(item)
