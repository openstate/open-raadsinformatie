import random
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan

from ocd_backend.utils.http import HttpRequestMixin
from requests import HTTPError

ES_BASE_URL = 'http://<ADMIN_URL>:9200/'
SAMPLE_SIZE = 1000
EXTRA_IDENTIFIERS = [9]

es = Elasticsearch(ES_BASE_URL)
max_count = es.count(index='_all')['count']

mixin = HttpRequestMixin()

identifier_sample = []
if SAMPLE_SIZE > 0:
    identifier_list = xrange(1, max_count)
    identifier_sample = random.sample(identifier_list, k=SAMPLE_SIZE)
identifier_sample.extend(EXTRA_IDENTIFIERS)
identifier_sample = list(set(identifier_sample))

ori_api_request_failed = []
ori_api_not_found = []
elastic_not_found = []
resource_not_found = []
resource_no_match = []
resource_type_match = []


elastic_response = scan(es, query={'query': {'ids': {'values': identifier_sample}}})
elastic_hits = {int(x['_id']): x['_source'] for x in elastic_response}

i = 1
for identifier in identifier_sample:
    if i % 100 == 0:
        print('Processing', i)
    i += 1

    full_identifier = 'https://id.openraadsinformatie.nl/%i' % identifier

    try:
        ori_api_response = mixin.http_session.get(full_identifier + '.jsonld')
    except HTTPError:
        ori_api_request_failed.append(identifier)
        continue

    try:
        elastic_content = elastic_hits[identifier]
    except KeyError:
        if ori_api_response.status_code == 404:
            resource_not_found.append(identifier)
            continue
        else:
            elastic_not_found.append(identifier)
            continue

    if ori_api_response.status_code == 404:
        ori_api_not_found.append(identifier)
        continue

    ori_api_response_json = ori_api_response.json()

    _, _, value = ori_api_response_json['@type'].rpartition(':')
    if value != elastic_content['@type']:
        resource_no_match.append(identifier)
        continue

    resource_type_match.append(identifier)


sample_size = len(identifier_sample)


def stats(text, stat_list):
    stat_count = len(stat_list)
    percent = (stat_count * 1.0 / sample_size) * 100

    print(text, stat_count, '{:.1f}%'.format(percent), stat_list)


print
print
print('Sample size', sample_size)
stats('ORI API request failed', ori_api_request_failed)
stats('ORI API not found', ori_api_not_found)
stats('Elastic not found', elastic_not_found)
stats('Resource not found', resource_not_found)
stats('Resource no match', resource_no_match)
stats('Resource type match', resource_type_match)
print
