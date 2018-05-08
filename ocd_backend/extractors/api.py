import json

from ocd_backend.extractors import BaseExtractor, HttpRequestMixin
from ocd_backend.log import get_source_logger
from ocd_backend.utils.api import FrontendAPIMixin

log = get_source_logger('extractor')


class FrontendAPIExtractor(BaseExtractor, HttpRequestMixin, FrontendAPIMixin):
    """
    Extracts items from the frontend API.
    """

    def run(self):
        results = self.api_request(self.source_definition['index_name'],
                                   self.source_definition['frontend_type'],
                                   **self.source_definition['frontend_args'])  # 100 for now ...

        for result in results:
            # log.debug("%s - %s" % (result['id'], result['classification'],))
            log.debug(u"%s - %s (%s)" % (result['start_date'], result['name'], result['id'],))
            yield 'application/json', json.dumps(result)
