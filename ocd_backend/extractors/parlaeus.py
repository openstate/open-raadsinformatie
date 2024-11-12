import json

from ocd_backend.extractors import BaseExtractor
from ocd_backend.log import get_source_logger

log = get_source_logger('extractor')


class ParlaeusMeetingsExtractor(BaseExtractor):
    """
    A meetings extractor for the Parlaeus API.
    """

    def __init__(self, *args, **kwargs):
        super(ParlaeusMeetingsExtractor, self).__init__(*args, **kwargs)
        self.base_url = self.source_definition['base_url']
        self.rid = self.source_definition['session_id']

    def get_response(self, url):
        response = self.http_session.get(url, timeout=(3, 5)).json()
        if response['status'] != 200:
            log.error(f'[{self.source_definition["key"]}] Parlaeus request error: {response["message"]}')
        return response

    def run(self):
        start_date, end_date = self.date_interval()
        url = f'{self.base_url}?rid={self.rid}&fn=agenda_list&since={start_date:%Y%m%d}&until={end_date:%Y%m%d}'
        response = self.get_response(url)

        for meeting in response.get('list', []):
            if not meeting['agid']:
                log.error(f'[{self.source_definition["key"]}] The value for "agid" seems to be empty, skipping')
                continue

            cached_path = 'agenda_detail/%s' % meeting['agid']

            url = '%s?fn=agenda_detail&agid=%s' % (
                self.base_url,
                meeting['agid'],
            )
            resp = self.http_session.get(url + '&rid=%s' % self.rid, timeout=(3, 5))
            resp.raise_for_status()

            meeting_data = resp.json()
            agenda = meeting_data['agenda']
            agenda['url'] = url

            if not self.check_if_most_recent('parlaeus', self.source_definition["key"], 'meeting', agenda, meeting['agid']):
                yield 'application/json', json.dumps(agenda), url, 'parlaeus/' + cached_path


class ParlaeusCommitteesExtractor(ParlaeusMeetingsExtractor):
    """
    Extracts committees from the Parlaeus API.
    """

    def run(self):
        cached_path = 'cie_list'
        url = f'{self.base_url}?rid={self.rid}&fn=cie_list'
        response = self.get_response(url)

        for committee in response.get('list', []):
            committee['url'] = url
            if not self.check_if_most_recent('parlaeus', self.source_definition["key"], 'committee', committee, committee['cmid']):
                yield 'application/json', json.dumps(committee), None, 'parlaeus/' + cached_path


class ParlaeusPersonsExtractor(ParlaeusMeetingsExtractor):
    """
    Extracts persons from the Parlaeus API.
    """

    def run(self):
        cached_path = 'person_list'
        url = f'{self.base_url}?rid={self.rid}&fn=person_list'
        response = self.get_response(url)

        for person in response.get('list', []):
            person['url'] = url
            if not self.check_if_most_recent('parlaeus', self.source_definition["key"], 'person', person, person['raid']):
                yield 'application/json', json.dumps(person), None, 'parlaeus/' + cached_path
