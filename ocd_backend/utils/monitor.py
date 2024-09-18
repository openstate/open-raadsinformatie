#!usr/bin/env python
from pprint import pprint

import requests
import json

from ocd_backend.es import elasticsearch as es
from ocd_backend.es import setup_elasticsearch

def get_indices():
    return [l.strip().split(" ")[2] for l in es.cat.indices().split("\n") if l != '']

def get_recent_counts():
    payload = {
        'query': {
            'bool': {
                'filter': [
                    {'term': {"@type": "MediaObject"}},
                    {'range': {
                        'last_discussed_at': {
                            'gte': 'now-30d'
                        }
                    }}
                ]
            }
        },
        "aggs": {
          "index": {
            "terms": {
                "field": "_index",
                "size": 10000
            }
          }
        },
        "size": 0
    }
    resp = es.search(body=payload)
    #print(resp)
    indices = get_indices()
    result = {i: 0 for i in indices}
    for b in resp.get('aggregations', {}).get('index', {}).get('buckets', []):
        result[b['key']] = b['doc_count']
    return result
