from celery import Celery

from ocd_backend.settings import CELERY_CONFIG

celery_app = Celery('ocd_backend', include=[
    'ocd_backend.pipeline',
    'ocd_backend.models',
    'ocd_backend.models.definitions',
    'ocd_backend.extractors',
    'ocd_backend.transformers.goapi_committee',
    'ocd_backend.transformers.goapi_meeting',
    'ocd_backend.transformers.gv',
    'ocd_backend.transformers.ibabs_committee',
    'ocd_backend.transformers.ibabs_meeting',
    'ocd_backend.transformers.ibabs_person',
    'ocd_backend.transformers.ibabs_report',
    'ocd_backend.transformers.notubiz_committee',
    'ocd_backend.transformers.notubiz_meeting',
    'ocd_backend.transformers.parlaeus_meeting',
    'ocd_backend.transformers.organizations',
    'ocd_backend.transformers.persons',
    'ocd_backend.enrichers.media_enricher',
    'ocd_backend.enrichers.media_enricher.static',
    'ocd_backend.loaders.elasticsearch',
    'ocd_backend.loaders.delta',
    'ocd_backend.tasks',
])

celery_app.conf.update(**CELERY_CONFIG)
