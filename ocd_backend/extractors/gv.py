import json
from pprint import pprint
import re
from hashlib import sha1

import requests

from ocd_backend.extractors import BaseExtractor

from ocd_backend import settings
from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.utils.api import FrontendAPIMixin
from ocd_backend.exceptions import ConfigurationError
from ocd_backend.log import get_source_logger

log = get_source_logger('extractor')


class GreenValleyBaseExtractor(BaseExtractor):
    def __init__(self, *args, **kwargs):
        super(GreenValleyBaseExtractor, self).__init__(*args, **kwargs)

        for opt in ['base_url', 'username', 'key', 'hash']:
            opt_key = 'greenvalley_%s' % (opt,)
            if opt_key not in self.source_definition:
                raise ConfigurationError('Missing \'%s\' definition' % (
                    opt_key,))

            if not self.source_definition[opt_key]:
                raise ConfigurationError('The \'%s\' is empty' % (opt_key,))

            setattr(self, opt, self.source_definition[opt_key])

    def _fetch(self, action, params={}):
        payload = {
            'username': self.username,
            'key': self.key,
            'hash': self.hash,
            'action': action
        }
        payload.update(params)
        return requests.get(self.base_url, params=payload, verify=False)


class GreenValleyExtractor(GreenValleyBaseExtractor):
    def _get_meta(self):
        return [
            {"metaname": "objecttype", "operator": "=", "type": "string",
                "values": ["agenda"]}]

    def run(self):
        params = {
            'start': 0,
            'count': int(
                self.source_definition.get('greenvalley_page_size', '5')),
            'meta': json.dumps(self._get_meta())
        }
        fetch_next_page = True

        while fetch_next_page:
            print "Fetching items, starting from %s ..." % (params['start'],)
            results = self._fetch('GetObjectsByQuery', params).json()
            pprint(results)
            for result in results['objects']:
                yield 'application/json', json.dumps(result)
            params['start'] += len(results['objects'])
            fetch_next_page = (len(results['objects']) > 0)
