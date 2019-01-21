import os

from ocd_backend.enrichers.media_enricher import MediaEnricher
from ocd_backend.log import get_source_logger
from ocd_backend.settings import DATA_DIR_PATH
from ocd_backend.utils.misc import get_sha1_hash
from ocd_backend.utils.http import LocalCachingMixin, GCSCachingMixin

log = get_source_logger('enricher')


class LocalStaticMediaEnricher(MediaEnricher, LocalCachingMixin):
    pass


class GCSStaticMediaEnricher(MediaEnricher, GCSCachingMixin):
    bucket_name = 'ori-static'
