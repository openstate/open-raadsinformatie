from math import ceil
from time import sleep
import json

from ocd_backend.extractors import BaseExtractor, HttpRequestMixin
from ocd_backend.extractors import log
from ocd_backend.exceptions import NotFound


class NPOJournalistiekExtractor(BaseExtractor, HttpRequestMixin):
    api_base_url = 'https://backstage-api.kro-ncrv.nl/content/'
    # The number of items to request in a single API call
    items_per_page = 100
    # Domain 1 is the top level in the NPO Journalistiek content
    # hierarchy and thus contains all content
    domain_id = 1
    # The 'fromDate' is required to retrieve detailed output. It is
    # currently mapped to an internal date field which is not returned
    # in the so simply use a static date for now.
    from_date = '2000-01-01'

    def api_call(self, url, params={}):
        params.update(
                pageSize=self.items_per_page,
                domainID=self.domain_id,
                fromDate=self.from_date,
        )
        url = '%s%s' % (self.api_base_url, url)

        log.debug('Getting %s (params: %s)' % (url, params))
        r = self.http_session.get(url, params=params, verify=False)
        r.raise_for_status()

        return r.json()

    def get_collection_objects(self):
        enough_items = True
        current_page = 0
        while enough_items:
            log.info('Getting collection items page %s', current_page)
            resp = self.api_call('get', params={
                'pageIndex': current_page
            })

            sleep(1)

            current_page += 1

            print len(resp)
            if len(resp) < self.items_per_page:
                enough_items = False

            for item in resp:
                yield item

    def run(self):
        for item in self.get_collection_objects():
            yield 'application/json', json.dumps(item)
