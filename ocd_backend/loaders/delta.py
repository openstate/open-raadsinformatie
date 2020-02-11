from urllib import parse
from confluent_kafka import Producer
from pyld import jsonld

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.loaders import BaseLoader
from ocd_backend.log import get_source_logger
from ocd_backend.models.serializers import JsonLDSerializer

log = get_source_logger('delta_loader')


class DeltaLoader(BaseLoader):
    """Serializes a model to N-Quads and then sends it to a Kafka bus."""

    config = {
        'bootstrap.servers': '%s:%s' % (settings.KAFKA_HOST, settings.KAFKA_PORT),
        'session.timeout.ms': settings.KAFKA_SESSION_TIMEOUT,
    }

    if settings.KAFKA_USERNAME:
        config['sasl.mechanisms'] = 'PLAIN'
        config['security.protocol'] = 'SASL_SSL'
        # config['ssl.ca.location'] = '/usr/local/etc/openssl/cert.pem'
        config['sasl.username'] = settings.KAFKA_USERNAME
        config['sasl.password'] = settings.KAFKA_PASSWORD

    def load_item(self, doc):

        # Skip this loader if it is disabled in settings
        if not settings.KAFKA_HOST or not settings.KAFKA_PORT:
            return

        kafka_producer = Producer(self.config)

        log_identifiers = []
        # Recursively index associated models like attachments
        for model in doc.traverse():
            self.add_metadata(model, doc == model)

            # Serialize the body to JSON-LD
            jsonld_body = JsonLDSerializer(loader_class=self).serialize(model)

            # Serialize the jsonld_body to N-Triples
            ntriples = jsonld.normalize(jsonld_body, {'algorithm': 'URDNA2015', 'format': 'application/n-quads'})

            # Add the graph name to the body. This is done the low-tech way, but could be improved by updating the
            # JSON-LD so that the graph information is included when serializing to N-Quads.
            ntriples_split = ntriples.split(' .\n')
            nquads = ' <http://purl.org/linked-delta/replace?graph={}> .\n'.format(
                parse.quote(model.get_ori_identifier())).join(ntriples_split)

            # Send document to the Kafka bus
            log_identifiers.append(model.get_short_identifier())
            message_key_id = '%s_%s' % (settings.KAFKA_MESSAGE_KEY, model.get_short_identifier())
            kafka_producer.produce(settings.KAFKA_TOPIC, nquads.encode('utf-8'), message_key_id, callback=delivery_report)

            # See https://github.com/confluentinc/confluent-kafka-python#usage for a complete example of how to use
            # the kafka producer with status callbacks.

        log.debug('DeltaLoader sending document ids to Kafka: %s' % ', '.join(log_identifiers))

        kafka_producer.flush()


def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        log.warning('Message delivery failed: {}'.format(err))


@celery_app.task(bind=True, base=DeltaLoader, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def delta_loader(self, *args, **kwargs):
    return self.start(*args, **kwargs)
