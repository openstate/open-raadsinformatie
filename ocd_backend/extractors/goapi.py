import json
from datetime import datetime
from urlparse import urljoin
from pprint import pprint

from ocd_backend.extractors import BaseExtractor
from ocd_backend.log import get_source_logger
from ocd_backend.utils.http import HttpRequestMixin

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
        log.info('Now retrieving: %s' % (urljoin(self.base_url, path),))
        resp = self.http_session.get(
            urljoin(self.base_url, path), verify=False)

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
        committee_count = 1
        total, static_json = self._request('dmus')
        for dmu in static_json:
            yield 'application/json', json.dumps(dmu)
            committee_count += 1

        log.info("Extracted total of %d committees." % committee_count)


class GemeenteOplossingenMeetingsExtractor(GemeenteOplossingenBaseExtractor):
    """
    Extracts meetings from the GemeenteOplossingen API.
    """

    def run(self):
        meeting_count = 0
        for start_date, end_date in self.interval_generator():
            url = 'meetings?date_from=%i&date_to=%i' % (
                    (start_date - datetime(1970, 1, 1)).total_seconds(),
                    (end_date - datetime(1970, 1, 1)).total_seconds()
                )
            total, static_json = self._request(url)

            for meeting in static_json:
                yield 'application/json', json.dumps(meeting)
                meeting_count += 1

            log.info("Now processing meetings from %s to %s" % (start_date, end_date,))
            log.info("Extracted total of %d meetings." % meeting_count)


# class GemeenteOplossingenMeetingItemsExtractor(GemeenteOplossingenBaseExtractor):
#     """
#     Extracts meeting items from the GemeenteOplossingen API.
#     """
#
#     def run(self):
#         meeting_count = 0
#         for start_date, end_date in self.interval_generator():
#
#             resp = self.http_session.get(
#                 u'%s/v1/meetings?date_from=%i&date_to=%i' % (
#                     self.base_url,
#                     (start_date - datetime(1970, 1, 1)).total_seconds(),
#                     (end_date - datetime(1970, 1, 1)).total_seconds()
#                 )
#             )
#
#             if resp.status_code == 200:
#                 static_json = json.loads(resp.content)
#
#                 for meeting in static_json:
#                     if 'items' in meeting:
#                         for item in meeting['items']:
#
#                             # Temporary hack to inherit meetingitem date from meeting
#                             if 'date' not in item:
#                                 item['date'] = meeting['date']
#
#                             kv = {meeting['id']: item}
#                             yield 'application/json', json.dumps(kv)
#                             meeting_count += 1
#
#             log.info("Now processing meetings from %s to %s" % (start_date, end_date,))
#             log.info("Extracted total of %d meetings." % meeting_count)


class GemeenteOplossingenDocumentsExtractor(GemeenteOplossingenBaseExtractor):
    """
    Extracts documents from the GemeenteOplossingen API.
    """

    def run(self):
        meeting_count = 0
        for start_date, end_date in self.interval_generator():

            total, docs = self._request(
                u'documents?publicationDate_from=%s&publicationDate_to=%s&limit=50000' % (
                    start_date.isoformat(),
                    end_date.isoformat()))

            for doc in docs:
                yield 'application/json', json.dumps(doc)
                meeting_count += 1

            log.info("Now processing documents from %s to %s" % (start_date, end_date,))
            log.info("Extracted total of %d documents." % meeting_count)
