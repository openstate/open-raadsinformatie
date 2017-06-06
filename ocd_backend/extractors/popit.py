import json

from ocd_backend.extractors import HttpRequestMixin
from .staticfile import StaticJSONExtractor


class PopItExtractor(StaticJSONExtractor, HttpRequestMixin):
    """
    Extract items from an OData Feed.
    """

    def extract_items(self, static_content):
        """
        Extracts items from the result of a popit call. Does paging.
        """

        static_json = json.loads(static_content)
        page_count = 1

        while static_json is not None:
            for item in static_json['result']:
                yield 'application/json', json.dumps(item)

            if static_json.get('next_url'):
                page_count += 1
                result = self.http_session.get(
                    static_json['next_url'])
                static_json = result.json()
            else:
                static_json = None  # force the end of the loop
