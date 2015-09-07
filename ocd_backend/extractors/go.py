import json
from pprint import pprint
import re

from lxml import etree
from suds.client import Client

from ocd_backend.extractors import BaseExtractor, HttpRequestMixin
from ocd_backend.exceptions import ConfigurationError

from ocd_backend import settings


class GemeenteOplossingenBaseExtractor(BaseExtractor, HttpRequestMixin):
    """
    A base extractor for scraping GemeenteOplossingen websites. This
    base extractor just configures the base url to use for scraping.
    """

    def __init__(self, *args, **kwargs):
        super(GemeenteOplossingenBaseExtractor, self).__init__(*args, **kwargs)

        self.base_url = self.source_definition['base_url']

    def _get_committees(self):
        """
        Gets a list of committees, along with links to upcoming and archived
        meetings.
        """

        committees = []

        resp = self.http_session.get(u'%s/Vergaderingen' % (self.base_url,))

        if resp.status_code != 200:
            return committees

        html = etree.HTML(resp.content)
        for c in html.xpath('//div[@class="orgaan block"]'):
            committee = {
                'name': u''.join(c.xpath('.//h3/text()')),
                'upcoming': u'%s%s' % (
                    self.base_url,
                    u''.join(c.xpath('.//li[@class="next"]/a/@href')),
                ),
                'archive': u'%s%s' % (
                    self.base_url,
                    u''.join(c.xpath('.//li[@class="prev"]/a/@href')),
                )
            }
            committees.append(committee)

        return committees


class GemeenteOplossingenCommitteesExtractor(GemeenteOplossingenBaseExtractor):
    """
    Extracts the committees from GemeenteOplossingenWebsites. This is done
    by scraping the meetings page and taking the meeting types which
    have 'commissies' in the title.
    """

    def run(self):
        committees = self._get_committees()
        # pprint(committees)

        for c in self._get_committees():
            yield 'application/json', json.dumps(c)


class GemeenteOplossingenMeetingsExtractor(GemeenteOplossingenBaseExtractor):
    def _get_upcoming_meetings(self, upcoming_url):
        """
        Gets a list of upcoming meetings from the URL specified.
        """

        resp = self.http_session.get(u'%s/Vergaderingen' % (self.base_url,))

        if resp.status_code != 200:
            return []

        html = etree.HTML(resp.content)

        return [{
            'title': a.xpath(
                './/span[@class="komendevergadering_title"]/text()'),
            'time': a.xpath(
                './/span[@class="komendevergadering_aanvang"]/text()'),
            'url': a.xpath(
                './/span[@class="komendevergadering_agenda"]/text()')
        } for a in html.xpath(
            '//div[@class="komendevergadering overview list_arrow"]')]

    def run(self):
        pages = [c['upcoming'] for c in self._get_committees()]

        for page in pages:
            for meeting in self._get_upcoming_meetings(page):
                yield 'application/json', json.dumps(meeting)
