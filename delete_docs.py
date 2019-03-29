#!/usr/bin/env python

import os
import sys

import redis
import requests

from elasticsearch import helpers as es_helpers
from elasticsearch.exceptions import RequestError

import ocd_backend
from ocd_backend.es import elasticsearch as es
from ocd_backend.utils.misc import reindex


def main():
    ids = [i.strip() for i in sys.stdin.readlines()]
    for i in ids:
        res = es.delete_by_query(index='ori_*', body={
            "query": {
                "match": {
                    "_id": i
                }
            },
            "size": 0})
        print res
    return 0

if __name__ == '__main__':
    sys.exit(main())
