import json
from datetime import datetime

from ocd_backend.extractors import BaseExtractor, HttpRequestMixin
from ocd_backend.log import get_source_logger

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

        self.base_url = self.source_definition['base_url']


class GemeenteOplossingenCommitteesExtractor(GemeenteOplossingenBaseExtractor):
    """
    Extracts committees from the GemeenteOplossingen API.
    """

    def run(self):
        resp = self.http_session.get(
            u'%s/dmus' % self.base_url)

        if resp.status_code == 200:
            static_json = json.loads(resp.content)
            self.total = len(static_json)

            for dmu in static_json:
                yield 'application/json', json.dumps(dmu)


class GemeenteOplossingenMeetingsExtractor(GemeenteOplossingenBaseExtractor):
    """
    Extracts meetings from the GemeenteOplossingen API.
    """

    def run(self):
        meeting_count = 0
        for start_date, end_date in self.interval_generator():

            resp = self.http_session.get(
                u'%s/meetings?date_from=%i&date_to=%i' % (
                    self.base_url,
                    (start_date - datetime(1970, 1, 1)).total_seconds(),
                    (end_date - datetime(1970, 1, 1)).total_seconds()
                )
            )

            if resp.status_code == 200:
                static_json = json.loads(resp.content)

                for meeting in static_json:
                    yield 'application/json', json.dumps(meeting)
                    meeting_count += 1

            log.info("Now processing meetings from %s to %s" % (start_date, end_date,))
            log.info("Extracted total of %d meetings." % meeting_count)


class GemeenteOplossingenMeetingItemsExtractor(GemeenteOplossingenBaseExtractor):
    """
    Extracts meeting items from the GemeenteOplossingen API.
    """

    def run(self):
        meeting_count = 0
        for start_date, end_date in self.interval_generator():

            resp = self.http_session.get(
                u'%s/meetings?date_from=%i&date_to=%i' % (
                    self.base_url,
                    (start_date - datetime(1970, 1, 1)).total_seconds(),
                    (end_date - datetime(1970, 1, 1)).total_seconds()
                )
            )

            if resp.status_code == 200:
                static_json = json.loads(resp.content)

                for meeting in static_json:
                    if 'items' in meeting:
                        for item in meeting['items']:

                            # Temporary hack to inherit meetingitem date from meeting
                            if 'date' not in item:
                                item['date'] = meeting['date']

                            kv = {meeting['id']: item}
                            yield 'application/json', json.dumps(kv)
                            meeting_count += 1

            log.info("Now processing meetings from %s to %s" % (start_date, end_date,))
            log.info("Extracted total of %d meetings." % meeting_count)
