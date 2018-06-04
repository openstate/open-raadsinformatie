import json

from dateutil.parser import parse
from ocd_backend.extractors import BaseExtractor, HttpRequestMixin
from ocd_backend.log import get_source_logger

log = get_source_logger('extractor')


class ParlaeusMeetingsExtractor(BaseExtractor, HttpRequestMixin):
    """
    A meetings extractor for the Parlaeus API.
    """

    def __init__(self, *args, **kwargs):
        super(ParlaeusMeetingsExtractor, self).__init__(*args, **kwargs)
        self.base_url = self.source_definition['base_url']
        self.rid = self.source_definition['session_id']

    def run(self):
        start_date, end_date = self.date_interval()
        resp = self.http_session.get(
            '%s?rid=%s&fn=agenda_list&since=%s&until=%s' % (
                self.base_url,
                self.rid,
                start_date.strftime("%Y%m%d"),
                end_date.strftime("%Y%m%d"),
            )
        )
        resp.raise_for_status()

        json_data = resp.json()
        meetings = json_data.get('list')

        for meeting in meetings:
            if not meeting['agid']:
                log.error("The value for 'agid' seems to be empty, skipping")
                continue

            url = '%s?rid=%s&fn=agenda_detail&agid=%s' % (
                self.base_url,
                self.rid,
                meeting['agid'],
            )
            resp = self.http_session.get(url)
            resp.raise_for_status()

            meeting_data = resp.json()
            agenda = meeting_data['agenda']
            agenda['url'] = url
            yield 'application/json', json.dumps(agenda)


class ParlaeusMeetingitemsExtractor(ParlaeusMeetingsExtractor, HttpRequestMixin):
    """
    A meetingitems extractor for the Parlaeus API.
    """

    def run(self):
        start_date, end_date = self.date_interval()
        resp = self.http_session.get(
            '%s?rid=%s&fn=agenda_list&since=%s&until=%s' % (
                self.base_url,
                self.rid,
                start_date.strftime("%Y%m%d"),
                end_date.strftime("%Y%m%d"),
            )
        )
        resp.raise_for_status()

        json_data = resp.json()
        meetings = json_data.get('list')

        for meeting in meetings:
            if not meeting['agid']:
                log.error("The value for 'agid' seems to be empty, skipping")
                continue

            url = '%s?rid=%s&fn=agenda_detail&agid=%s' % (
                self.base_url,
                self.rid,
                meeting['agid'],
            )
            resp = self.http_session.get(url)
            resp.raise_for_status()

            meeting_data = resp.json()

            for meeting_item in meeting_data['agenda']['points']:
                meeting_item['parent'] = meeting_data['agenda']['agid']
                meeting_item['url'] = url
                yield 'application/json', json.dumps(meeting_item)


class ParlaeusCommitteesExtractor(ParlaeusMeetingsExtractor):
    """
    Extracts committees from the Parleaus API.
    """

    def run(self):
        url = '%s?rid=%s&fn=cie_list' % (
            self.base_url,
            self.rid,
        )
        resp = self.http_session.get(url)
        resp.raise_for_status()

        json_data = resp.json()
        for committee in json_data.get('list'):
            committee['url'] = url
            yield 'application/json', json.dumps(committee)


class ParlaeusPersonsExtractor(ParlaeusMeetingsExtractor):
    """
    Extracts persons from the Parleaus API.
    """

    def run(self):
        url = '%s?rid=%s&fn=person_list' % (
            self.base_url,
            self.rid,
        )
        resp = self.http_session.get(url)
        resp.raise_for_status()

        json_data = resp.json()
        for person in json_data.get('list'):
            person['url'] = url
            yield 'application/json', json.dumps(person)
