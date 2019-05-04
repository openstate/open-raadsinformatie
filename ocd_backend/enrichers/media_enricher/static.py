from ocd_backend.enrichers.media_enricher import MediaEnricher
from ocd_backend.log import get_source_logger
from ocd_backend.utils.http import HttpRequestMixin, LocalCachingMixin, GCSCachingMixin

log = get_source_logger('enricher')


class TemporaryFileMediaEnricher(MediaEnricher, HttpRequestMixin):
    pass


class LocalStaticMediaEnricher(MediaEnricher, LocalCachingMixin):
    pass


class GCSStaticMediaEnricher(MediaEnricher, GCSCachingMixin):
    bucket_name = 'ori-static'
