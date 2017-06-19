# This config file is mounted into the celery container, see docker-compose.yml

# Register custom serializer for Celery that allows for encoding and decoding
# Python datetime objects (and potentially other ones)
from kombu.serialization import register
from serializers import encoder, decoder

register('ocd_serializer', encoder, decoder, content_encoding='binary',
         content_type='application/ocd-msgpack')

CELERY_CONFIG = {
    'BROKER_URL': 'redis://redis:6379/0',
    'CELERY_ACCEPT_CONTENT': ['ocd_serializer'],
    'CELERY_TASK_SERIALIZER': 'ocd_serializer',
    'CELERY_RESULT_SERIALIZER': 'ocd_serializer',
    'CELERY_RESULT_BACKEND': 'ocd_backend.result_backends:OCDRedisBackend+redis://redis:6379/0',
    'CELERY_IGNORE_RESULT': True,
    'CELERY_DISABLE_RATE_LIMITS': True,
    # Expire results after 30 minutes; otherwise Redis will keep
    # claiming memory for a day
    'CELERY_TASK_RESULT_EXPIRES': 1800
}
