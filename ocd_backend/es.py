import json

from elasticsearch import Elasticsearch, serializer, compat, exceptions

from ocd_backend.settings import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT


class JSONSerializerPython2(serializer.JSONSerializer):
    """Override elasticsearch library serializer to ensure it encodes utf characters during json dump.
    See original at: https://github.com/elastic/elasticsearch-py/blob/master/elasticsearch/serializer.py#L42
    A description of how ensure_ascii encodes unicode characters to ensure they can be sent across the wire
    as ascii can be found here: https://docs.python.org/2/library/json.html#basic-usage
    """

    def dumps(self, data):
        # don't serialize strings
        if isinstance(data, compat.string_types):
            return data
        try:
            return json.dumps(data, default=self.default, ensure_ascii=True)
        except (ValueError, TypeError) as e:
            raise exceptions.SerializationError(data, e)


def setup_elasticsearch(host=ELASTICSEARCH_HOST, port=ELASTICSEARCH_PORT):
    return Elasticsearch([{'host': host, 'port': port, 'timeout': 20}],
                         serializer=JSONSerializerPython2())


elasticsearch = setup_elasticsearch()
