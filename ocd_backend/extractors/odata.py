import json
import os

from ocd_backend import settings
from ocd_backend.log import get_source_logger
from .staticfile import StaticJSONExtractor

log = get_source_logger('extractor')


class ODataExtractor(StaticJSONExtractor):
    """
    Extract items from an OData Feed.
    """

    def extract_items(self, static_content):
        """
        Extracts items from a JSON file. It is assumed to be an array
        of items.
        """
        static_json = {'value': []}

        gem_path = os.path.abspath(
            os.path.join(settings.PROJECT_PATH, 'json', 'gemeenten.json'))
        with open(gem_path) as gem_file:
            static_json = json.load(gem_file)

        item_filter = self.source_definition['filter']
        log.debug("[%s] OData searching for: %s" % (self.source_definition['sitename'], item_filter,))

        for item in static_json['value']:
            # log.debug(item)
            passed_filter = (item_filter is None) or (
                item[item_filter.keys()[0]] == item_filter.values()[0])

            if passed_filter:
                log.debug(item)
                yield 'application/json', json.dumps(item)
