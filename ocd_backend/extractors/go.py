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

        resp = self.http_session.get(upcoming_url)

        if resp.status_code != 200:
            return []

        html = etree.HTML(resp.content)

        committee = u''.join(html.xpath('//h1/text()')).replace(
            u'Komende vergaderingen ', u'').strip()

        return [{
            'committee': committee,
            'title': u''.join(a.xpath(
                './/span[@class="komendevergadering_title"]/text()')),
            'time': u''.join(a.xpath(
                './/span[@class="komendevergadering_aanvang"]/text()')),
            'url': u'%s%s' % (
                self.base_url,
                u''.join(a.xpath(
                    './/span[@class="komendevergadering_agenda"]/a/@href')),)
        } for a in html.xpath(
            '//div[@class="komendevergadering overview list_arrow"]')]

    def run(self):
        pages = [c['upcoming'] for c in self._get_committees()][:1] # for now ...

        for page in pages:
            for meeting in self._get_upcoming_meetings(page)[:1]:
                print meeting['url']
                resp = self.http_session.get(meeting['url'])
                if resp.status_code != 200:
                    continue

                html = etree.HTML(resp.content)

                # we need to get the print url too as it contains more info
                print_url = u'%s/print' % (meeting['url'],)
                print_resp = self.http_session.get(print_url)

                if print_resp.status_code != 200:
                    continue

                # this is a bit ugly, but saves us from having to scrape
                # all the meeting pages twice ...

                meeting_obj = 'application/json', {
                    'type': 'meeting',
                    'content': etree.tostring(html),
                    'full_content': resp.content,
                    'print_content': print_resp.content
                }

                yield 'application/json', meeting_obj

                for meeting_item_html in html.xpath(
                    '//li[contains(@class, "agendaRow")]'):
                        meeting_item_obj = {
                            'type': 'meeting-item',
                            'content': etree.tostring(meeting_item_html),
                            'full_content': resp.content,
                            'print_content': print_resp.content
                        }

                        yield 'application/json', meeting_item_obj
