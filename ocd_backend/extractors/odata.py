import json
from pprint import pprint

from .staticfile import StaticJSONExtractor


class ODataExtractor(StaticJSONExtractor):
    """
    Extract items from an OData Feed.
    """

    def extract_items(self, static_content):
        """
        Extracts items from a JSON file. It is assumed to be an array
        of items.
        """
        static_json = json.loads(static_content)
        item_filter = self.source_definition['filter']
        # print "Searching for: %s" % (item_filter,)

        for item in static_json['value']:
            # pprint(item)
            passed_filter = (item_filter is None) or (
                item[item_filter.keys()[0]] == item_filter.values()[0])

            if passed_filter:
                pprint(item)
                yield 'application/json', json.dumps(item)
