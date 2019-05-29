from pyld import jsonld
from confluent_kafka import Producer

from ocd_backend import settings
from ocd_backend.log import get_source_logger
from ocd_backend.models.serializers import JsonLDSerializer
from ocd_backend.loaders import BaseLoader

log = get_source_logger('delta_loader')


class DeltaLoader(BaseLoader):
    """Serializes a model to N-Quads and then sends it to a Kafka bus."""

    config = {
        'bootstrap.servers': settings.KAFKA_HOST,
        'session.timeout.ms': settings.KAFKA_SESSION_TIMEOUT,
        'group.id': settings.KAFKA_GROUP
    }

    if settings.KAFKA_USERNAME:
        config['api.version.request'] = True
        config['broker.version.fallback'] = '0.10.0.0'
        config['api.version.fallback.ms'] = 0
        config['sasl.mechanisms'] = 'PLAIN'
        config['security.protocol'] = 'SASL_SSL'
        # config['ssl.ca.location'] = '/usr/local/etc/openssl/cert.pem'
        config['sasl.username'] = settings.KAFKA_USERNAME
        config['sasl.password'] = settings.KAFKA_PASSWORD

    kafka_producer = Producer(config)

    def load_item(self, doc):
        # Recursively index associated models like attachments
        for model in doc.traverse():
            # Serialize the body to JSON-LD
            jsonld_body = JsonLDSerializer().serialize(model)

            # Serialize the jsonld_body to N-Triples
            ntriples = jsonld.normalize(jsonld_body, {'algorithm': 'URDNA2015', 'format': 'application/n-quads'})

            # Add the graph name to the body. This is done the low-tech way, but could be improved by updating the
            # JSON-LD so that the graph information is included when serializing to N-Quads.
            ntriples_split = ntriples.split(' .\n')
            nquads = ' <http://purl.org/link-lib/supplant> .\n'.join(ntriples_split)

            # Send document to the Kafka bus
            log.debug('DeltaLoader sending document id %s to Kafka' % model.get_ori_identifier())
            self.kafka_producer.produce(settings.KAFKA_TOPIC, nquads.encode('utf-8'))

            # See https://github.com/confluentinc/confluent-kafka-python#usage for a complete example of how to use
            # the kafka producer with status callbacks.
