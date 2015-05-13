from lxml import etree
from io import StringIO, BytesIO
from time import sleep
import datetime
import json

from ocd_backend.extractors import BaseExtractor, HttpRequestMixin
from ocd_backend.extractors import log
from ocd_backend.exceptions import NotFound


class PRIDExtractor(BaseExtractor, HttpRequestMixin):
    npo_base_url = 'http://npo.nl/'
    delta = datetime.timedelta(days=1)

    def npo_call(self, url, params={}):
        url = '%s%s' % (self.npo_base_url, url)
        log.debug('Getting %s (params: %s)' % (url, params))
        r = self.http_session.get(url, params=params)
        r.raise_for_status()
        return r.text

    def get_npo_programs(self):
        date = datetime.datetime.strptime(
            self.source_definition['start_date'],
            '%Y-%m-%d'
        ).date()
        end_date = datetime.date.today()

        parser = etree.HTMLParser()

        while date <= end_date:
            print date.strftime("%Y-%m-%d")
            items_left = True
            current_page = 1

            while items_left:
                log.info('Getting npo items page %s', current_page)
                sleep(1)
                html = self.npo_call('zoeken', params={
                    'sort_date_period': date,
                    'page': current_page
                })

                PRIDs = {}
                tree = etree.parse(StringIO(html), parser)
                URLs = tree.xpath(
                    '//div[@class="list-item non-responsive row-fluid"]/div/' \
                    'a/@href'
                )

                if not URLs:
                    items_left = False
                current_page += 1

                for URL in URLs:
                    paths = URL.split('/')
                    PRIDs['PRID'] = paths[-1]
                    PRIDs['broadcast_date'] = paths[-2]
                    PRIDs['program_name'] = paths[-3]
                    yield PRIDs

            date += self.delta

    def run(self):
        for item in self.get_npo_programs():
            yield 'application/json', json.dumps(item)
