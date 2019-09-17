#!/usr/bin/env python

import simplejson as json
import sys
from optparse import OptionParser

from ocd_backend.es import elasticsearch as es
from ocd_backend.utils.misc import reindex


def transform_to_same(h):
    print "Transforming item %s ..." % (h['_id'],)
    # pprint(h)
    return h


def transform_to_old(h):
    if h['_type'] == u'events' and h['_source']['classification'] == u'Meetingitem':
        h['_source']['classification'] = u'Meeting Item'
    return h


def transform_to_new(h):
    if h['_type'] != u'events':
        return h

    # This needs to be translated
    if h['_source']['classification'] == u'Meeting Item':
        h['_source']['classification'] = u'Agendapunt'
    if h['_source']['classification'] == u'Meetingitem':
        h['_source']['classification'] = u'Agendapunt'
    if h['_source']['classification'] == u'Meeting':
        h['_source']['classification'] = u'Agenda'

    if 'source_data' in h['_source']:
        sd = h['_source']['source_data']
    else:
        try:
            doc = es.get(index=u'ori_%s' % (h['_source']['meta']['collection'],),
                         doc_type=h['_type'], id=h['_id'], _source_include=['*'])
            sd = doc['_source']['source_data']
            h['_source']['source_data'] = sd
        except Exception as e:
            sd = {}

    if h['_source']['classification'] != u'Report':
        return h

    if 'content_type' in sd and sd[u'content_type'] == u'application/json':
        # FIXME: this is mainly for iBabs, but what about GemeenteOplossingen?
        data = json.loads(sd['data'])

        if '_ReportName' in data:
            h['_source']['classification'] = unicode(
                data['_ReportName'].split(r'\s+')[0])
        elif h['_source']['classification'] == u'Report':
            h['_source']['classification'] = u'Verslag'
        elif h['_source']['classification'] == u'Resolution':
            h['_source']['classification'] = u'Besluitenlijst'

    return h


def run(argv):
    parser = OptionParser()
    parser.add_option("-a", "--action", dest="action", default="same",
                      help="perform ACTION", metavar="ACTION")
    parser.add_option("-i", "--index", dest="index", default='ori_heerde',
                      help="read from INDEX", metavar="INDEX")
    parser.add_option("-o", "--output", dest="output", default='ori_heerde_goed',
                      help="read from FILE", metavar="FILE")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", default=True,
                      help="don't print status messages to stdout")
    (options, args) = parser.parse_args()
    # reindex(es, options.index, options.output, transformation_callable=dummy_transform)

    func = None

    try:
        func = globals()["transform_to_%s" % (options.action,)]
    except KeyError as e:
        pass

    if func is None:
        return 1

    if not callable(func):
        return 2

    reindex(es, options.index, options.output, transformation_callable=func)
    return 0


if __name__ == '__main__':
    sys.exit(run(sys.argv))
