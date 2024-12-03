import json
from time import sleep
from urllib import parse

from ocd_backend.exceptions import ConfigurationError
from ocd_backend.extractors import BaseExtractor
from ocd_backend.log import get_source_logger
from ocd_backend.utils.http import HttpRequestMixin
from ocd_backend.utils.misc import strip_scheme

log = get_source_logger('extractor')


class GreenValleyBaseExtractor(BaseExtractor, HttpRequestMixin):
    def __init__(self, *args, **kwargs):
        super(GreenValleyBaseExtractor, self).__init__(*args, **kwargs)

        self.base_url = None
        self.username = None
        self.key = None
        self.hash = None

        for opt in ['base_url', 'username', 'key', 'hash']:
            opt_key = 'greenvalley_%s' % (opt,)
            if opt_key not in self.source_definition:
                raise ConfigurationError('Missing \'%s\' definition' % (
                    opt_key,))

            if not self.source_definition[opt_key]:
                raise ConfigurationError('The \'%s\' is empty' % (opt_key,))

            setattr(self, opt, self.source_definition[opt_key])

    def _url(self, action, params):
        params['action'] = action
        return '{}?{}'.format(self.base_url, parse.urlencode(params))

    def _fetch(self, url):
        auth = {
            'username': self.username,
            'key': self.key,
            'hash': self.hash,
        }
        return self.http_session.get('{}&{}'.format(url, parse.urlencode(auth)), timeout=(3, 5), verify=False)


class GreenValleyExtractor(GreenValleyBaseExtractor):
    def _get_meta(self):
        return [
            {"metaname": "objecttype", "operator": "=", "type": "string",
                "values": self.source_definition['greenvalley_objecttypes']}]

    def _get_items(self, response):
        return [response]

    def run(self):
        params = {
            'start': 0,
            'count': int(
                self.source_definition.get('greenvalley_page_size', '5')),
            'meta': json.dumps(self._get_meta())
        }
        fetch_next_page = True

        while fetch_next_page:
            sleep(self.source_definition.get('greenvalley_extract_timeout', 5))
            log.info(f'[{self.source_definition["key"]}] Fetching items, starting from {params["start"]}')
            url = self._url('GetModelsByQuery', params)
            cached_path = strip_scheme(url)
            results = self._fetch(url).json()
            log.info(f'[{self.source_definition["key"]}] Got {len(results["objects"])} items')
            for result in results['objects']:
                log.info(f'[{self.source_definition["key"]}] Object {result["default"]["objecttype"]}/'
                         f'{result["default"]["objectname"]} has {len(result.get("attachmentlist", []))} '
                         f'attachments and {len(result.get("SETS", []))} sets')

                for k, v in result.get('SETS', {}).items():
                    v['parent_objectid'] = result['default']['objectid']
                    v['bis_vergaderdatum'] = result['default']['bis_vergaderdatum']

                    result2 = {'default': v}
                    # identifier = result2['default']['objectid']
                    yield 'application/json', json.dumps(result2), None, 'greenvalley/' + cached_path

                # identifier = result['default']['objectid']
                yield 'application/json', json.dumps(result), None, 'greenvalley/' + cached_path

            params['start'] += len(results['objects'])
            fetch_next_page = (len(results['objects']) > 0)


class GreenValleyMeetingsExtractor(GreenValleyExtractor):
    def _get_meta(self):
        return [
            {
                "metaname": "objecttype",
                "operator": "=",
                "type": "string",
                "values": self.source_definition['greenvalley_objecttypes']
                # ["agenda"]
            }, {
                "metaname": self.source_definition.get(
                    'greenvalley_date_key', "bis_vergaderdatum"),
                "operator": ">",
                "type": "date",
                "values": ["%s000" % (self.start_date.strftime('%s'),)]
            }, {
                "metaname": self.source_definition.get(
                    'greenvalley_date_key', "bis_vergaderdatum"),
                "operator": "<",
                "type": "date",
                "values": ["%s000" % (self.end_date.strftime('%s'),)]
            }
        ]

    def run(self):
        self.start_date = None
        self.end_date = None
        for cur_start, cur_end in self.interval_generator():
            if self.start_date is None:
                self.start_date = cur_start
            self.end_date = cur_end
        log.debug(f'[{self.source_definition["key"]}] Now processing meetings from {self.start_date} to {self.end_date}')

        total_meetings = 0
        for item in super(GreenValleyMeetingsExtractor, self).run():
            ot = ",".join(self.source_definition['greenvalley_objecttypes'])
            mt = json.loads(item[1])
            hash_for_item = self.hash_for_item('gv', self.source_definition["key"], ot, item[1], mt['objectid'])
            if hash_for_item:
                yield item[0], item[1], item[2], item[3], hash_for_item
                total_meetings += 1

        log.info(f'[{self.source_definition["key"]}] Extracting total of {total_meetings} GreenValley meetings')
