from elasticsearch import Elasticsearch
from lxml import etree
from io import StringIO, BytesIO
from time import sleep
import datetime
import json
import re

from ocd_backend.extractors import BaseExtractor, HttpRequestMixin
from ocd_backend.extractors import log
from ocd_backend.exceptions import NotFound
from ocd_backend.settings import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT


class PRIDExtractor(BaseExtractor, HttpRequestMixin):
    npo_base_url = 'http://npo.nl/'
    delta = datetime.timedelta(days=1)

    def call(self, url, params={}):
        url = '%s%s' % (self.npo_base_url, url)
        log.debug('Getting %s (params: %s)' % (url, params))
        r = self.http_session.get(url, params=params)
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

    def get_npo_programs_by_prid(self):
        # Retrieve the PRIDs from the PRID index. This assumes that the
        # PRID source has already been extracted.
        es = Elasticsearch(
            hosts='%s:%s' % (ELASTICSEARCH_HOST, ELASTICSEARCH_PORT)
        )

        journalistiek_prids = self.get_items(es, 'npo_journalistiek', 'prid')
        prids = self.get_items(es, 'npo_prid', 'prid')

        new_prids = journalistiek_prids - prids

        parser = etree.HTMLParser()
        len_prids = len(new_prids)
        for idx, PRID in enumerate(new_prids):
            print 'Downloading PRID %s/%s: %s' % (idx, len_prids, PRID)
            html = self.call(PRID)
            tree = etree.parse(StringIO(html), parser)

            data = {}
            # Retrieve program URLs listed on the webpage and
            # extract the PRID and program slug
            URL = tree.xpath('//meta[@name="og:url"]/@content')
            # If there is no URL, then there is most likely no NPO.nl
            # page for this PRID, so don't continue
            if not URL:
                continue
            paths = URL[0].split('/')
            data['prid'] = paths[-1]
            data['program_slug'] = paths[-3]

            # Retrieve program website
            website = tree.xpath(
                '//div[@class="dark-well meta-data-box"]/a/@href'
            )
            if website:
                data['website'] = website[0]

            # Retrieve dates of each program
            broadcast_date = tree.xpath(
                '//div[@class="dark-well meta-data-box"]/'
                'div[@class="data"]/div[@class="broadcast-time"]/text()'
            )[0].strip()
            # The text field sometimes contains some extra info
            # besides the date; filter out just the date as the
            # other info is availabe in the metadata
            match = re.search(
                '(\w{2} \d{1,2} \w{3} \d{4} \d{2}:\d{2})',
                broadcast_date
            )
            data['broadcast_date'] = match.group(0)

            # Retrieve program names
            data['program_name'] = tree.xpath(
                '//meta[@name="og:title"]/@content'
            )[0]

            # Retrieve program image
            images = tree.xpath('//meta[@name="og:image"]/@content')
            # Some programs don't have an image
            if images:
                data['image'] = images

            # Retrieve description
            data['description'] = tree.xpath(
                '//meta[@name="description"]/@content'
            )[0]

            # Retrieve genres
            genres = []
            genre = tree.xpath(
                '//div[@class="dark-well meta-data-box"]/div[@class="data"]'
                '/div[@class="genres"]/text()'
            )[0].split()
            if ' en ' in genre:
                (head, tail) = genre.split(' en ')
                if ',' in head:
                    for x in head.split(', '):
                        genres.append(x)
                    genres.append(tail)
                else:
                    genres.append(head)
                    genres.append(tail)
            else:
                genres.append(genre)
            if genres:
                data['genres'] = genres

            # Retrieve ratings
            ratings = tree.xpath(
                '//div[@class="dark-well meta-data-box"]/div[@class="data"]'
                '/div[@class="ratings"]/span/@title'
            )
            if ratings:
                data['ratings'] = ratings

            yield data

    def get_npo_programs_by_date(self):
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
                html = self.call('zoeken', params={
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
                    # Some programs don't have an image
                    if images:
                        data['image'] = eval(images[0])

                    yield data

            date += self.delta

    def run(self):
        extract_type = self.source_definition['extract_type']
        if extract_type == 'by_date':
            for item in self.get_npo_programs_by_date():
                yield 'application/json', json.dumps(item)
        elif extract_type == 'by_prid':
            for item in self.get_npo_programs_by_prid():
                yield 'application/json', json.dumps(item)
