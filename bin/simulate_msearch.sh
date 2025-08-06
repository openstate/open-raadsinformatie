#!/bin/bash
# Simulate openbesluitvorming.nl queries; attempt to improve performance on new server
#
# Queries taken from openbesluitvorming.nl call, and changed the `_source` parameter from
#       "_source":{"includes":["*"],"excludes":[]}
# to
#       "_source":{"includes":["*"],"excludes":["md_text","text_pages"]}

SEARCH_TERM=$1
IP_ADDRESS=`sudo docker inspect ori_elastic_1 | grep IPAddress | tail -1 | awk -F "\"" '{print $4}'`
curl -XGET $IP_ADDRESS:9200/*/_msearch -H 'Content-Type: application/x-ndjson' -d '
{"preference":"organisaties"}
{"query":{"bool":{"must":[{"bool":{"must":[{"bool":{"must":[{"multi_match":{"fields":["text","title","description","name"],"type":"best_fields","operator":"OR","query":"'$SEARCH_TERM'"}},{"terms":{"_index":["ori_*","osi_*","owi_*"]}},{"term":{"@type":"MediaObject"}}],"must_not":[{"match":{"@type":"Membership"}}]}}]}}]}},"highlight":{"pre_tags":["<mark>"],"post_tags":["</mark>"],"fields":{"text":{},"title":{},"name":{},"description":{}},"fragment_size":100,"number_of_fragments":3},"size":0,"_source":{"includes":["*"],"excludes":["md_text","text_pages"]},"aggs":{"_index":{"terms":{"field":"_index","size":500,"order":{"_count":"desc"}}}}}
{"preference":"thema"}
{"query":{"bool":{"must":[{"bool":{"must":[{"bool":{"must":[{"multi_match":{"fields":["text","title","description","name"],"type":"best_fields","operator":"OR","query":"'$SEARCH_TERM'"}},{"terms":{"_index":["ori_*","osi_*","owi_*"]}},{"term":{"@type":"MediaObject"}}],"must_not":[{"match":{"@type":"Membership"}}]}}]}}]}},"highlight":{"pre_tags":["<mark>"],"post_tags":["</mark>"],"fields":{"text":{},"title":{},"name":{},"description":{}},"fragment_size":100,"number_of_fragments":3},"size":0,"_source":{"includes":["*"],"excludes":["md_text","text_pages"]},"aggs":{"tags.http://www.w3.org/1999/02/22-rdf-syntax-ns#_8.https://argu.co/ns/meeting/tag.keyword":{"terms":{"field":"tags.http://www.w3.org/1999/02/22-rdf-syntax-ns#_8.https://argu.co/ns/meeting/tag.keyword","size":500,"order":{"_count":"desc"}}}}}
{"preference":"ResultList01"}
{"query":{"bool":{"must":[{"bool":{"must":[{"bool":{"must":[{"multi_match":{"fields":["text","title","description","name"],"type":"best_fields","operator":"OR","query":"'$SEARCH_TERM'"}},{"terms":{"_index":["ori_*","osi_*","owi_*"]}},{"term":{"@type":"MediaObject"}}],"must_not":[{"match":{"@type":"Membership"}}]}}]}}]}},"highlight":{"pre_tags":["<mark>"],"post_tags":["</mark>"],"fields":{"text":{},"title":{},"name":{},"description":{}},"fragment_size":100,"number_of_fragments":3},"size":20,"_source":{"includes":["*"],"excludes":["md_text","text_pages"]},"sort":[{"last_discussed_at":{"order":"desc"}}]}
'

# Original queries:
# {"preference":"organisaties"}
# {"query":{"bool":{"must":[{"bool":{"must":[{"bool":{"must":[{"multi_match":{"fields":["text","title","description","name"],"type":"best_fields","operator":"OR","query":"'$SEARCH_TERM'"}},{"terms":{"_index":["ori_*","osi_*","owi_*"]}},{"term":{"@type":"MediaObject"}}],"must_not":[{"match":{"@type":"Membership"}}]}}]}}]}},"highlight":{"pre_tags":["<mark>"],"post_tags":["</mark>"],"fields":{"text":{},"title":{},"name":{},"description":{}},"fragment_size":100,"number_of_fragments":3},"size":0,"_source":{"includes":["*"],"excludes":[]},"aggs":{"_index":{"terms":{"field":"_index","size":500,"order":{"_count":"desc"}}}}}
# {"preference":"thema"}
# {"query":{"bool":{"must":[{"bool":{"must":[{"bool":{"must":[{"multi_match":{"fields":["text","title","description","name"],"type":"best_fields","operator":"OR","query":"'$SEARCH_TERM'"}},{"terms":{"_index":["ori_*","osi_*","owi_*"]}},{"term":{"@type":"MediaObject"}}],"must_not":[{"match":{"@type":"Membership"}}]}}]}}]}},"highlight":{"pre_tags":["<mark>"],"post_tags":["</mark>"],"fields":{"text":{},"title":{},"name":{},"description":{}},"fragment_size":100,"number_of_fragments":3},"size":0,"_source":{"includes":["*"],"excludes":[]},"aggs":{"tags.http://www.w3.org/1999/02/22-rdf-syntax-ns#_8.https://argu.co/ns/meeting/tag.keyword":{"terms":{"field":"tags.http://www.w3.org/1999/02/22-rdf-syntax-ns#_8.https://argu.co/ns/meeting/tag.keyword","size":500,"order":{"_count":"desc"}}}}}
# {"preference":"ResultList01"}
# {"query":{"bool":{"must":[{"bool":{"must":[{"bool":{"must":[{"multi_match":{"fields":["text","title","description","name"],"type":"best_fields","operator":"OR","query":"'$SEARCH_TERM'"}},{"terms":{"_index":["ori_*","osi_*","owi_*"]}},{"term":{"@type":"MediaObject"}}],"must_not":[{"match":{"@type":"Membership"}}]}}]}}]}},"highlight":{"pre_tags":["<mark>"],"post_tags":["</mark>"],"fields":{"text":{},"title":{},"name":{},"description":{}},"fragment_size":100,"number_of_fragments":3},"size":20,"_source":{"includes":["*"],"excludes":[]},"sort":[{"last_discussed_at":{"order":"desc"}}]}
