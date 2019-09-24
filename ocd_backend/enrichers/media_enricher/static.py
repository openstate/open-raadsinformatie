from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.enrichers.media_enricher import MediaEnricher
from ocd_backend.log import get_source_logger
from ocd_backend.utils.http import HttpRequestMixin, GCSCachingMixin

log = get_source_logger('enricher')


class TemporaryFileMediaEnricher(MediaEnricher, HttpRequestMixin):
    pass


class GCSStaticMediaEnricher(MediaEnricher, GCSCachingMixin):
    bucket_name = 'ori-static'


@celery_app.task(bind=True, base=TemporaryFileMediaEnricher, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def temporary_file_media_enricher(self, *args, **kwargs):
    return self.start(*args, **kwargs)


@celery_app.task(bind=True, base=GCSStaticMediaEnricher, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def gcs_static_media_enricher(self, *args, **kwargs):
    return self.start(*args, **kwargs)
