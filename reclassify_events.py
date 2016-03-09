#!/usr/bin/env python

import sys
import os
import re
import json
from pprint import pprint
from collections import OrderedDict
from optparse import OptionParser

import redis

from elasticsearch import helpers as es_helpers
from elasticsearch.exceptions import RequestError

import ocd_backend
from ocd_backend.es import elasticsearch as es
from ocd_backend.utils.misc import reindex


def dummy_transform(h):
    print "Transforming item %s ..." % (h['_id'],)
    pprint(h)
    return h

def transform_to_old(h):
    if h['_type'] == u'events' and h['_source']['classification'] == u'Meetingitem':
        h['_source']['classification'] = u'Meeting Item'
    return h

def transform_to_new(h):
    if h['_type'] != u'events':
        return h

    if h['_source']['classification'] == u'Meeting Item':
        h['_source']['classification'] = u'Meetingitem'

    if h['_source'].has_key('source_data') and h['_source']['classification'] == u'Report':
        sd = h['_source']['source_data']
        if sd[u'content_type'] ==  u'application/json':
            data = json.loads(sd['data'])
            h['_source']['classification'] = unicode(data['_ReportName'].split(r'\s+')[0])

    return h

def run(argv):
    parser = OptionParser()
    parser.add_option("-i", "--index", dest="index", default='ori_heerde',
                      help="read from INDEX", metavar="INDEX")
    parser.add_option("-o", "--output", dest="output", default='ori_heerde_goed',
                      help="read from FILE", metavar="FILE")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", default=True,
                      help="don't print status messages to stdout")
    (options, args) = parser.parse_args()
    #reindex(es, options.index, options.output, transformation_callable=dummy_transform)
    reindex(es, options.index, options.output, transformation_callable=transform_to_new)
    return 0

if __name__ == '__main__':
    sys.exit(run(sys.argv))
