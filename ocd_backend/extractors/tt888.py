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

    # TODO: This function should use better elasticsearch querying
    def get_items(self, es, index, field):
        field_string = ','.join(field)
        scroll = es.search(
            index=index,
            scroll='5m',
            search_type='scan',
            fields=field_string
        )
        scroll_id = scroll['_scroll_id']
        items_left = scroll['hits']['total']

        items = []
        while items_left > 0:
            results = es.scroll(scroll_id=scroll_id, scroll='5m')
            items_left -= len(results['hits']['hits'])
            for hit in results['hits']['hits']:
                field_data = {}
                if 'fields' not in hit:
                    continue

                if len(field) > 1:
                    for f in field:
                        field_data[f] = hit['fields'][f][0]
                    items.append(field_data)
                else:
                    items.append(hit['fields'][field_string][0])

        return items

    def get_subtitles(self):
        # Retrieve the PRIDs from the PRID index. This assumes that the
        # PRID source has already been extracted.
        es = Elasticsearch(
            hosts='%s:%s' % (ELASTICSEARCH_HOST, ELASTICSEARCH_PORT)
        )

        metadata_tt888_prids = []
        metadata_prids = self.get_items(es, 'npo_metadata', ['prid', 'tt888'])
        for item in metadata_prids:
            if item['tt888'] == 'ja':
                metadata_tt888_prids.append(item['prid'])

        tt888_prids = self.get_items(es, 'npo_tt888', ['prid'])

        new_prids = set(metadata_tt888_prids) - set(tt888_prids)

        len_prids = len(new_prids)
        for idx, PRID in enumerate(new_prids):
            print 'Downloading PRID %s/%s: %s' % (idx + 1, len_prids, PRID)
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
