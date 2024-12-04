#!/bin/bash
# Usage:
# - without parameters it returns the sum of filesizes of documents for all indexes (in TB)
#   ./bin/total_filesizes.sh
# - if you're interested only in 1 index supply it, e.g. (in GB)
#   ./bin/total_filesizes.sh ori_zutphen_20241112153328
if [ -z "$1" ]; then
  DIVIDE='/ 1024 / 1024 / 1024 / 1024'
  UNITS='TB'
  QUERY_STRING=''
else  
  DIVIDE='/ 1024 / 1024 / 1024'
  UNITS='GB'
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
        "filesizes": {
          "sum": {
            "field": "size_in_bytes"
          }
        }
      }
    }
  }
}' |jq '.aggregations.index.buckets| map(.filesizes.value) | add '"$DIVIDE" | awk -v units=" $UNITS" '{print $1 units}'

# Total on 04-12-2024: 4564506884403 ~ 4.251GB ~ 4.2TB