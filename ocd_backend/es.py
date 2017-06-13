from elasticsearch import Elasticsearch

from ocd_backend.settings import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT


def setup_elasticsearch(host=ELASTICSEARCH_HOST, port=ELASTICSEARCH_PORT):
    return Elasticsearch([{'host': host, 'port': port}])


elasticsearch = setup_elasticsearch()
