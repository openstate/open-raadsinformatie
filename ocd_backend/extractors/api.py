import json
from pprint import pprint
import re

from ocd_backend.extractors import BaseExtractor, HttpRequestMixin
from ocd_backend.exceptions import ConfigurationError
from ocd_backend.utils.api import FrontendAPIMixin

from ocd_backend import settings


class FrontendAPIExtractor(BaseExtractor, HttpRequestMixin, FrontendAPIMixin):
    """
    Extracts items from the frontend API.
    """
    def run(self):
        results = self.api_request(self.source_definition['index_name'],
            self.source_definition['frontend_type'],
            **self.source_definition['frontend_args'])  # 100 for now ...

        for result in results:
            # print u"%s - %s (%s)" % (result['start_date'], result['name'], result['id'],)
            yield 'application/json', json.dumps(result)
