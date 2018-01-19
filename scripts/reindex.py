#!/usr/bin/env python

import os
import sys
import re
from pprint import pprint
from time import sleep

from elasticsearch.helpers import scan, bulk
backend_path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    '..')

sys.path.insert(0, backend_path)

import ocd_backend
from ocd_backend import settings
from ocd_backend.es import elasticsearch


def get_aliases():
    result = {}
    for l in elasticsearch.cat.aliases().split(u'\n'):
        fields = re.split(r'\s+', l)
        if len(fields) > 1:
            result[fields[0]] = fields[1]
    return result


def copy_index(es_alias, es_index):
        items = scan(
            elasticsearch,
            query=None,
            scroll='5m',
            size=10,
            raise_on_error=False, index=es_index)

        new_index = u'%s_migrated' % (es_index,)
        new_items = []
        for item in items:
            item['_index'] = new_index
            del item['_score']
            new_items.append(item)
        bulk(elasticsearch, new_items, chunk_size=10)
        sleep(5)
        print "%s (%s) -> %s" % (es_alias, es_index, new_index,)
        try:
            elasticsearch.indices.delete_alias(index='_all', name=es_alias)
        except Exception as e:
            pass  # did not have alias
        try:
            elasticsearch.indices.put_alias(index=new_index, name=es_alias)
        except Exception as e:
            print "Could not set alias for %s (%s) -> %s" % (es_alias, es_index, new_index,)
            print e.message

def main():
    for es_alias, es_index in get_aliases().iteritems():
        if not es_index.endswith('_migrated'):
            copy_index(es_alias, es_index)
    return 0

if __name__ == '__main__':
    sys.exit(main())
