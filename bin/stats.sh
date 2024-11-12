#!/bin/bash
# Usage:
# - without parameters it returns counts for all indexes
#   ./bin/stats
# - if you're interested only in 1 index supply it, e.g.
#   ./bin/stats ori_zutphen_20241112153328
if [ -z "$1" ]; then
  QUERY_STRING=''
else  
  read -d '\n' QUERY_STRING << EndOfQuery
  "query": {
    "simple_query_string": {
      "fields": ["_index"],
      "query": "$1"
    }
  },
EndOfQuery
fi

curl -s -H 'Content-type: application/json' 'https://api.openraadsinformatie.nl/v1/elastic/_search' -d '{
  "size": 0,
  '"$QUERY_STRING"'
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
