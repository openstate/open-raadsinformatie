from elasticsearch import Elasticsearch
from time import sleep
import json

from ocd_backend.extractors import BaseExtractor, HttpRequestMixin
from ocd_backend.extractors import log
from ocd_backend.exceptions import NotFound


class MetadataExtractor(BaseExtractor, HttpRequestMixin):
    metadata_base_url = 'http://e.omroep.nl/metadata/'

    def call(self, url):
        url = '%s%s' % (self.metadata_base_url, url)
        log.debug('Getting %s' % (url))
        r = self.http_session.get(url)
        r.raise_for_status()
        return r.text

    def get_metadata(self):
        # Retrieve the PRIDs from the PRID index. Thi assumes that the
        # PRID source has been processed before.
        es = Elasticsearch(hosts='127.0.0.1:9200')
        scroll = es.search(
            index='ocd_prid',
            scroll='1m',
            search_type='scan',
            fields='PRID'
        )

        scroll_id = scroll['_scroll_id']
        scroll_size = scroll['hits']['total']

        while scroll_size > 0:
            results = es.scroll(scroll_id=scroll_id, scroll='1m')
            scroll_size = len(results['hits']['hits'])
            for hit in results['hits']['hits']:
                PRID = hit['fields']['PRID'][0]
                metadata = self.call(PRID)
                metadata = metadata.split("\n")[0][14:-1]
                try:
                    metadata_json = json.loads(metadata)
                except ValueError, e:
                    print 'Invalid metadata JSON: ' + str(e)
                    continue
                yield metadata_json


        #while date <= end_date:
        #    print date.strftime("%Y-%m-%d")
        #    items_left = True
        #    current_page = 1

        #    while items_left:
        #        log.info('Getting npo items page %s', current_page)
        #        sleep(1)
        #        html = self.npo_call('zoeken')

        #        PRIDs = {}
        #        tree = etree.parse(StringIO(html), parser)
        #        URLs = tree.xpath(
        #            '//div[@class="list-item non-responsive row-fluid"]/div/' \
        #            'a/@href'
        #        )

        #        if not URLs:
        #            items_left = False
        #        current_page += 1

        #        for URL in URLs:
        #            paths = URL.split('/')
        #            PRIDs['PRID'] = paths[-1]
        #            PRIDs['broadcast_date'] = paths[-2]
        #            PRIDs['program_name'] = paths[-3]
        #            yield PRIDs

        #    date += self.delta

    def run(self):
        for item in self.get_metadata():
            yield 'application/json', json.dumps(item)
