import json

from ocd_backend.extractors import BaseExtractor, HttpRequestMixin


class GemeenteOplossingenBaseExtractor(BaseExtractor, HttpRequestMixin):
    """
    A base extractor for the GemeenteOplossingen API. This base extractor just
    configures the base url to use for accessing the API.
    """

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
        resp = self.http_session.get(
            u'%s/meetings' % self.base_url)

        if resp.status_code == 200:
            static_json = json.loads(resp.content)
            self.total = len(static_json)

            for meeting in static_json:
                yield 'application/json', json.dumps(meeting)


class GemeenteOplossingenMeetingItemsExtractor(
        GemeenteOplossingenBaseExtractor):
    """
    Extracts meeting items from the GemeenteOplossingen API.
    """

    def run(self):
        resp = self.http_session.get(
            u'%s/meetings' % self.base_url)

        if resp.status_code == 200:
            static_json = json.loads(resp.content)
            self.total = len(static_json)

            for meeting in static_json:
                if 'items' in meeting:
                    for item in meeting['items']:
                        kv = {meeting['id']: item}
                        yield 'application/json', json.dumps(kv)
