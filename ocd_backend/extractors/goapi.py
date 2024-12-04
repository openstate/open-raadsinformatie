import json
from datetime import datetime
from urllib.parse import urljoin

from ocd_backend.extractors import BaseExtractor
from ocd_backend.log import get_source_logger
from ocd_backend.utils.http import HttpRequestMixin
from ocd_backend.utils.misc import strip_scheme

log = get_source_logger('extractor')


class GemeenteOplossingenBaseExtractor(BaseExtractor, HttpRequestMixin):
    """
    A base extractor for the GemeenteOplossingen API. This base extractor just
    configures the base url to use for accessing the API.
    """

    def run(self):
        pass

    def __init__(self, *args, **kwargs):
        super(GemeenteOplossingenBaseExtractor, self).__init__(*args, **kwargs)

        self.api_version = self.source_definition.get('api_version', 'v1')
        self.base_url = '%s/%s/' % (
            self.source_definition['base_url'], self.api_version,)

    def _request(self, path):
        log.debug(f'Now retrieving: {urljoin(self.base_url, path)}')
        resp = self.http_session.get(
            urljoin(self.base_url, path), timeout=(3, 5), verify=False)

        if resp.status_code == 200:
            static_json = json.loads(resp.content)
            if self.api_version == 'v1':
                return len(static_json), static_json
            else:
                # V2 api has meta data in the outer object and the results
                # in an inner key which depends on the call being made
                parts = path.split('/')
                if len(parts) > 1:
                    model = parts[0]
                else:
                    model = path.split('?')[0]
                return (
                    int(static_json['result']['totalCount']),
                    static_json['result'][model],)
        else:
            return (0, [],)


class GemeenteOplossingenCommitteesExtractor(GemeenteOplossingenBaseExtractor):
    """
    Extracts committees from the GemeenteOplossingen API.
    """

    def run(self):
        committee_count = 0
        committees_skipped = 0

        cached_path = strip_scheme(urljoin(self.base_url, 'dmus'))

        total, static_json = self._request('dmus')
        for dmu in static_json:
            hash_for_item = self.hash_for_item('go', self.source_definition["key"], 'committee', dmu['id'], dmu)
            if hash_for_item:
                yield 'application/json', \
                      json.dumps(dmu), \
                      urljoin(self.base_url, 'dmus'), \
                      'gemeenteoplossingen/' + cached_path, \
                      hash_for_item
                committee_count += 1
            else:
                committees_skipped += 1

        log.info(f'[{self.source_definition["key"]}] Extracted total of {committee_count} GO API committees. '
                 f'Also skipped {committees_skipped} GO API committees')


class GemeenteOplossingenMeetingsExtractor(GemeenteOplossingenBaseExtractor):
    """
    Extracts meetings from the GemeenteOplossingen API.
    """

    def run(self):
        meeting_count = 0
        meetings_skipped = 0

        for start_date, end_date in self.interval_generator():
            # v2 requires dates in YYYY-MM-DD format, instead of a unix timestamp
            if self.source_definition.get('api_version') == 'v2':
                url = 'meetings?date_from=%s&date_to=%s' % (
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
            else:
                url = 'meetings?date_from=%i&date_to=%i' % (
                    (start_date - datetime(1970, 1, 1)).total_seconds(),
                    (end_date - datetime(1970, 1, 1)).total_seconds()
                )
            cached_path = strip_scheme(urljoin(self.base_url, url))
            total, static_json = self._request(url)

            for meeting in static_json:
                hash_for_item = self.hash_for_item('go', self.source_definition["key"], 'meeting', meeting['id'], meeting)
                if hash_for_item:
                    yield 'application/json', \
                          json.dumps(meeting), \
                          None, \
                          'gemeenteoplossingen/' + cached_path, \
                          hash_for_item
                    meeting_count += 1
                else:
                    meetings_skipped += 1

            log.debug(f'[{self.source_definition["key"]}] Now processing meetings from {start_date} to {end_date}')
        log.info(f'[{self.source_definition["key"]}] Extracted total of {meeting_count} GO API meetings. '
                 f'Also skipped {meetings_skipped} GO API meetings')


# class GemeenteOplossingenMeetingItemsExtractor(GemeenteOplossingenBaseExtractor):
#     """
#     Extracts meeting items from the GemeenteOplossingen API.
#     """
#
#     def run(self):
#         meeting_count = 0
#         for start_date, end_date in self.interval_generator():
#             url = 'meetings?date_from=%i&date_to=%i' % (
#                     (start_date - datetime(1970, 1, 1)).total_seconds(),
#                     (end_date - datetime(1970, 1, 1)).total_seconds()
#                 )
#
#             total, static_json = self._request(url)
#             for meeting in static_json:
#                 if 'items' in meeting:
#                     for item in meeting['items']:
#
#                         # Temporary hack to inherit meetingitem date from meeting
#                         if 'date' not in item:
#                             item['date'] = meeting['date']
#
#                         kv = {meeting['id']: item}
#                         yield 'application/json', json.dumps(kv)
#                         meeting_count += 1
#
#             log.info("Now processing meeting items from %s to %s" % (start_date, end_date,))
#             log.info("Extracted total of %d meeting items." % meeting_count)


class GemeenteOplossingenDocumentsExtractor(GemeenteOplossingenBaseExtractor):
    """
    Extracts documents from the GemeenteOplossingen API.
    """

    def run(self):
        document_count = 0
        documents_skipped = 0

        for start_date, end_date in self.interval_generator():
            url = 'documents?publicationDate_from=%s&publicationDate_to=%s&limit=50000' % (
                start_date.isoformat(),
                end_date.isoformat()
            )
            cached_path = strip_scheme(urljoin(self.base_url, url))

            total, docs = self._request(url)

            for doc in docs:
                api_version = self.source_definition.get('api_version', 'v1')
                base_url = '%s/%s' % (self.source_definition['base_url'], api_version,)
                hash_for_item = self.hash_for_item('go', self.source_definition["key"], 'document', doc['id'], doc)
                if hash_for_item:
                    yield 'application/json', \
                          json.dumps(doc), \
                          '%s/documents/%i' % (base_url, doc['id']), \
                          'gemeenteoplossingen/' + cached_path, \
                          hash_for_item
                    document_count += 1
                else:
                    documents_skipped += 1

            log.debug(f'[{self.source_definition["key"]}] Now processing documents from {start_date} to {end_date}')
        log.info(f'[{self.source_definition["key"]}] Extracted total of {document_count} GO API documents. '
                 f'Also skipped {documents_skipped} GO API documents')
