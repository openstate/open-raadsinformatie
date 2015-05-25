from lxml import etree
from io import StringIO, BytesIO
from time import sleep
import datetime
import json
import re

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
        base_xpath = '//div[@class="list-item non-responsive row-fluid"]'

        while date <= end_date:
            print date.strftime("%Y-%m-%d")
            items_left = True
            current_page = 1

            while items_left:
                log.info('Getting npo items page %s', current_page)
                sleep(1)
                html = self.npo_call('zoeken', params={
                    'sort_date_period': date,
                    'page': current_page,
                    'view': 'tile'
                })
                current_page += 1

                tree = etree.parse(StringIO(html), parser)
                items = tree.xpath(base_xpath)
                if not items:
                    items_left = False
                    continue

                for item in tree.xpath(base_xpath):
                    data = {}

                    # Retrieve dates of each program
                    broadcast_date = item.xpath(
                        'div[@class="span8"]/a/h5/text()'
                    )[0]
                    # The text field sometimes contains some extra info
                    # besides the date; filter out just the date as the
                    # other info is availabe in the metadata
                    match = re.search(
                        '(\w{2} \d{1,2} \w{3} \d{4} \d{2}:\d{2})',
                        broadcast_date
                    )
                    data['broadcast_date'] = match.group(0)

                    # Retrieve broadcaster(s) of each program
                    broadcasters = []
                    raw_broadcaster = item.xpath(
                        'div[@class="span8"]/a/h4/span[@class="inactive"]'
                        '/text()'
                    )[0]
                    # Remove parenthesis as the text looks like '(NOS)'
                    raw_broadcaster = raw_broadcaster[1:-1]
                    # Some programs are a collaboration between multiple
                    # broadcasters, e.g. '(NOS, VARA en VPRO)'
                    if ' en ' in raw_broadcaster:
                        (head, tail) = raw_broadcaster.split(' en ')
                        if ',' in head:
                            for x in head.split(', '):
                                broadcasters.append(x)
                            broadcasters.append(tail)
                        else:
                            broadcasters.append(head)
                            broadcasters.append(tail)
                    else:
                        broadcasters.append(raw_broadcaster)
                    data['broadcasters'] = broadcasters

                    # Retrieve program names
                    data['program_name'] = ''.join(
                        item.xpath('div[@class="span8"]/a/h4/text()')
                    ).strip()

                    # Retrieve program URLs listed on the webpage and
                    # extract the PRID and program slug
                    URL = item.xpath('div[@class="span8"]/a/@href')[0]
                    paths = URL.split('/')
                    data['prid'] = paths[-1]
                    data['program_slug'] = paths[-3]

                    # Retrieve program image
                    images = item.xpath(
                        'div[@class="span4"]/div[@class="image-container"]/a/'
                        'img/@data-images'
                    )
                    # Some programs don't have a image
                    if images:
                        data['image'] = eval(images[0])

                    yield data

            date += self.delta

    def run(self):
        for item in self.get_npo_programs():
            yield 'application/json', json.dumps(item)
