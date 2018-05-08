#!/usr/bin/env python
import json

import requests

with open('old-indices.txt') as in_file:
    indices = [x.strip() for x in in_file.readlines()]

for idx in indices:
    data = {
        "source": {
            "remote": {"host": "http://c-open-raadsinformatie:9200"},
            "index": idx,
            "size": 25,
        },
        "dest": {
            "index": idx
        }
    }
    print requests.post('http://elasticsearch:9200/_reindex', data=json.dumps(data)).content
