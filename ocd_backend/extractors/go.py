import json
from time import sleep

from lxml import etree

from ocd_backend.extractors import BaseExtractor
from ocd_backend.log import get_source_logger
from ocd_backend.utils.http import HttpRequestMixin

log = get_source_logger('extractor')


class GemeenteOplossingenBaseExtractor(BaseExtractor, HttpRequestMixin):
    """
    A base extractor for scraping GemeenteOplossingen websites. This
    base extractor just configures the base url to use for scraping.
    """

    def run(self):
        pass

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
        # log.debug(committees)

        total_committees = 0
        for c in committees:
            yield 'application/json', json.dumps(c)
            total_committees += 1

        log.info("[%s] Extracted a total of %d GO scraper committees" % (self.source_definition['index_name'], total_committees))


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

    def _get_archived_meetings(self, archive_url):
        """
        Gets a list of archived meetings from the URL specified.
        """

        resp = self.http_session.get(archive_url)

        if resp.status_code != 200:
            return []

        html = etree.HTML(resp.content)

        committee = u''.join(html.xpath('//div[@id="breadcrumb"]/strong//text()')).strip()

        return [{
            'committee': committee,
            'title': u''.join(a.xpath('.//text()')),
            'url': u'%s%s' % (self.base_url, u''.join(a.xpath('.//@href')),)
        } for a in html.xpath('//ul[@id="vergaderingen"]//li/a')]

    def _get_pages(self):
        if self.source_definition.get('upcoming', True):
            field = 'upcoming'
        else:
            field = 'archive'
        return [c[field] for c in self._get_committees()]  # for now ...

    def filter_meeting(self, meeting, html):
        """
        Should return true if the meeting is to be yielded.
        """

        return True

    def run(self):
        pages = self._get_pages()

        total_meetings = 0
        for page in pages:
            if self.source_definition.get('upcoming', True):
                meetings = self._get_upcoming_meetings(page)
            else:
                meetings = self._get_archived_meetings(page)

            for meeting in meetings:
                sleep(1)

                resp = self.http_session.get(meeting['url'])
                if resp.status_code != 200:
                    continue

                html = etree.HTML(resp.content)

                if not self.filter_meeting(meeting, html):
                    continue

                # this is a bit ugly, but saves us from having to scrape
                # all the meeting pages twice ...

                meeting_obj = {
                    'type': 'meeting',
                    'content': etree.tostring(html),
                    'full_content': resp.content,
                }

                yield 'application/json', json.dumps(meeting_obj)
                total_meetings += 1

                if not self.source_definition.get('extract_meeting_items', False):
                    continue

                for meeting_item_html in html.xpath(
                        '//li[contains(@class, "agendaRow")]'):
                    meeting_item_obj = {
                        'type': 'meeting-item',
                        'content': etree.tostring(meeting_item_html),
                        'full_content': resp.content,
                    }

                    yield 'application/json', json.dumps(meeting_item_obj)

        log.info("[%s] Extracted a total of %d GO scraper meetings" % (self.source_definition['index_name'], total_meetings))


class GemeenteOplossingenResolutionsExtractor(GemeenteOplossingenMeetingsExtractor):
    def filter_meeting(self, meeting, html):
        for item in html.xpath('//div[@id="documenten"]//li'):
            anchor = u''.join(item.xpath('.//a//text()'))
            if u'Besluitenlijst' in anchor:
                return True
        return False


class GemeenteOplossingenReportsExtractor(GemeenteOplossingenMeetingsExtractor):
    def filter_meeting(self, meeting, html):
        # for item in html.xpath('//div[@id="downloaden"]//li'):
        #     anchor = u''.join(item.xpath('.//a//@href'))
        #     if u'/mp3' in anchor:
        #         return True
        return True
