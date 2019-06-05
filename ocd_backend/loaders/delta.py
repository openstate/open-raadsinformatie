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
    }

    if settings.KAFKA_USERNAME:
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
            message_key_id = '%s_%s' % (settings.KAFKA_MESSAGE_KEY, model.get_ori_identifier())
            self.kafka_producer.produce(settings.KAFKA_TOPIC, nquads.encode('utf-8'), message_key_id, callback=delivery_report)
            self.kafka_producer.flush()

            # See https://github.com/confluentinc/confluent-kafka-python#usage for a complete example of how to use
            # the kafka producer with status callbacks.


def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        log.warning('Message delivery failed: {}'.format(err))
    else:
        log.debug('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))
