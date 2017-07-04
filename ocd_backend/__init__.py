from celery import Celery

from ocd_backend.settings import CELERY_CONFIG

celery_app = Celery('ocd_backend', include=[
    'ocd_backend.extractors',
    'ocd_backend.extractors.ggm',
    'ocd_backend.transformers',
    'ocd_backend.transformers.ggm',
    'ocd_backend.enrichers.media_enricher',
    'ocd_backend.enrichers.media_enricher.static',
    'ocd_backend.loaders',
    'ocd_backend.loaders.ggm',
    'ocd_backend.loaders.file',
    'ocd_backend.tasks'
])

celery_app.conf.update(**CELERY_CONFIG)
