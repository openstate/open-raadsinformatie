import json

from ocd_backend.extractors import BaseExtractor
from ocd_backend.log import get_source_logger
from ocd_backend.utils.http import GCSCachingMixin

log = get_source_logger('extractor')


class ParlaeusMeetingsExtractor(BaseExtractor, GCSCachingMixin):
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
        for meeting in json_data.get('list', []):
            if not meeting['agid']:
                log.error("The value for 'agid' seems to be empty, skipping")
                continue

            cached_path = 'agenda_detail/%s' % meeting['agid']

            url = '%s?fn=agenda_detail&agid=%s' % (
                self.base_url,
                meeting['agid'],
            )
            resp = self.http_session.get(url + '&rid=%s' % self.rid)
            resp.raise_for_status()

            meeting_data = resp.json()
            agenda = meeting_data['agenda']
            agenda['url'] = url
            yield 'application/json', json.dumps(agenda), url, 'parlaeus/' + cached_path


class ParlaeusCommitteesExtractor(ParlaeusMeetingsExtractor):
    """
    Extracts committees from the Parleaus API.
    """

    def run(self):
        cached_path = 'cie_list'

        url = '%s?rid=%s&fn=cie_list' % (
            self.base_url,
            self.rid,
        )
        resp = self.http_session.get(url)
        resp.raise_for_status()

        json_data = resp.json()
        for committee in json_data.get('list', []):
            committee['url'] = url
            yield 'application/json', json.dumps(committee), None, 'parlaeus/' + cached_path


class ParlaeusPersonsExtractor(ParlaeusMeetingsExtractor):
    """
    Extracts persons from the Parleaus API.
    """

    def run(self):
        cached_path = 'person_list'

        url = '%s?rid=%s&fn=person_list' % (
            self.base_url,
            self.rid,
        )
        resp = self.http_session.get(url)
        resp.raise_for_status()

        json_data = resp.json()
        for person in json_data.get('list', []):
            person['url'] = url
            yield 'application/json', json.dumps(person), None, 'parlaeus/' + cached_path
