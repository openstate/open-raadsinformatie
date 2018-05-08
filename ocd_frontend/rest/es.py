from elasticsearch import Elasticsearch


class ElasticsearchService(object):
    def __init__(self, host, port):
        self._es = Elasticsearch([{'host': host, 'port': port}])

    def search(self, *args, **kwargs):
        return self._es.search(*args, **kwargs)

    def create(self, *args, **kwargs):
        return self._es.index(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self._es.get(*args, **kwargs)

    def exists(self, *args, **kwargs):
        return self._es.exists(*args, **kwargs)

    def msearch(self, *args, **kwargs):
        return self._es.msearch(*args, **kwargs)

    def get_esclient(self):
        return self._es
