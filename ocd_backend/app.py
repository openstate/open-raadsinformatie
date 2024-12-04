import os

import sentry_sdk
from celery import Celery, signals

from ocd_backend.settings import CELERY_CONFIG, SENTRY_DSN, SENTRY_ENVIRONMENT

celery_app = Celery('ocd_backend', include=[
    'ocd_backend.pipeline',
    'ocd_backend.models',
    'ocd_backend.models.definitions',
    'ocd_backend.extractors',
    'ocd_backend.extractors.ggm',
    'ocd_backend.transformers.allmanak_organization',
    'ocd_backend.transformers.gedeputeerdestaten',
    'ocd_backend.transformers.ggm_committee',
    'ocd_backend.transformers.ggm_meeting',
    'ocd_backend.transformers.goapi_committee',
    'ocd_backend.transformers.goapi_meeting',
    'ocd_backend.transformers.greenvalley',
    'ocd_backend.transformers.ibabs_committee',
    'ocd_backend.transformers.ibabs_meeting',
    'ocd_backend.transformers.ibabs_report',
    'ocd_backend.transformers.notubiz_committee',
    'ocd_backend.transformers.notubiz_meeting',
    'ocd_backend.transformers.parlaeus_committee',
    'ocd_backend.transformers.parlaeus_meeting',
    'ocd_backend.transformers.database',
    'ocd_backend.enrichers.media_enricher',
    'ocd_backend.enrichers.text_enricher',
    'ocd_backend.loaders.elasticsearch',
    'ocd_backend.tasks',
])

celery_app.conf.update(**CELERY_CONFIG)

#@signals.worker_init.connect
@signals.celeryd_init.connect
def init_sentry(**_kwargs):
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        environment=SENTRY_ENVIRONMENT
    )  # same as above
