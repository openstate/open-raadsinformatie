#!/bin/bash
curl -s -H 'Content-type: application/json' 'https://api.openraadsinformatie.nl/v1/elastic/_search' -d '{
  "size": 0,
  "aggs": {
    "index": {
      "terms": {
        "field": "_index",
        "size": 1000
      },
      "aggs": {
        "documents": {
          "date_histogram": {
            "field": "start_date",
            "calendar_interval": "year"
          }
        }
      }
    }
  }
}' |jq '.aggregations.index.buckets[] |.key as $gm |.doc_count as $gm_total |{} as $gm_counts |.documents.buckets |map({name: $gm, (.key_as_string[:4]): .doc_count}) |add'
