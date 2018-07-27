import json
from pprint import pprint
import re
from hashlib import sha1
from time import sleep

import requests

from ocd_backend.extractors import BaseExtractor

from ocd_backend import settings
from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.utils.api import FrontendAPIMixin
from ocd_backend.exceptions import ConfigurationError
from ocd_backend.log import get_source_logger

log = get_source_logger('extractor')


def printTree(tree, depth=0):
    if tree is None or len(tree) == 0:
        print " " * depth, "-"
    else:
        try:
            items = tree.items()
        except AttributeError as e:
            items = []
        for key, val in items:
            print " " * depth, key
            printTree(val, depth+1)


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
            print "Fetching items, starting from %s ..." % (params['start'],)
            results = self._fetch('GetModelsByQuery', params).json()
            print "Got %s items ..." % (len(results['objects']),)
            for result in results['objects']:
                #pprint(result)
                print "Object %s/%s has %s SETS and %s attachnments" % (
                    result[u'default'][u'objecttype'],
                    result[u'default'][u'objectname'],
                    len(result.get(u'attachmentlist', [])),
                    len(result.get(u'SETS', [])),)
                if len(result.get(u'SETS', [])):
                    print "Sets:"
                    for key, osett in result[u'SETS'].iteritems():
                        print "* %s %s/%s" % (
                            osett[u'nodeorder'], osett[u'objecttype'],
                            osett[u'objectname'],)
                if len(result.get(u'attachmentlist', [])) > 0:
                    print "Attachments:"
                    for att_key, att in result[u'attachmentlist'].iteritems():
                        print "* %s/%s" % (
                            att[u'objecttype'], att[u'objectname'],)

                for k, v in result.get(u'SETS', {}).iteritems():
                    v[u'parent_objectid'] = result[u'default'][u'objectid']
                    v[u'bis_vergaderdatum'] = result[
                        u'default'][u'bis_vergaderdatum']

                    result = {u'default': v}
                    yield 'application/json', json.dumps(result)

                yield 'application/json', json.dumps(result)

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
                "metaname": "bis_vergaderdatum",
                "operator": ">",
                "type": "date",
                "values": ["%s000" % (self.start_date.strftime('%s'),)]
            }, {
                "metaname": "bis_vergaderdatum",
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
        log.info("%s: Now processing meetings from %s to %s" % (
            self.source_definition['key'], self.start_date, self.end_date,))
        for item in super(GreenValleyMeetingsExtractor, self).run():
            yield item
