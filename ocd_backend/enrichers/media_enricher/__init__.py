import urllib

import requests

from ocd_backend.app import celery_app
from ocd_backend.enrichers import BaseEnricher
from ocd_backend.exceptions import SkipEnrichment
from ocd_backend.log import get_source_logger
from ocd_backend.settings import RESOLVER_BASE_URL, AUTORETRY_EXCEPTIONS
from ocd_backend.utils.http import GCSCachingMixin
from ocd_backend.utils.misc import strip_scheme
from tasks.image_metadata import ImageMetadata

log = get_source_logger('enricher')


class MediaEnricher(BaseEnricher, GCSCachingMixin):
    """An enricher that is responsible for enriching external media
    (images, audio, video, etc.)

    Media items are fetched from the source and then passed on to a
    set of registered tasks that are responsible for the analysis.
    """

    #: The registry of available sub-tasks that are responsible for the
    #: analysis of media items.
    bucket_name = 'ori-static'

    available_tasks = {
        'image_metadata': ImageMetadata,
    }

    def enrich_item(self, item):
        """Enriches the media objects referenced in a single item.

        First, a media item will be retrieved from the source, than the
        registered and configured tasks will run. In case fetching the
        item fails, enrichment of the media item will be skipped. In case
        a specific media enrichment task fails, only that task is
        skipped, which means that we move on to the next task.
        """

        try:
            identifier = strip_scheme(item.identifier_url)
        except AttributeError:
            raise Exception('No identifier_url for item: %s', item)

        try:
            date_modified = item.date_modified
        except AttributeError:
            date_modified = None

        try:
            resource = self.fetch(
                item.original_url,
                identifier,
                date_modified,
            )
        except requests.HTTPError as e:
            raise SkipEnrichment(e)

        item.url = '%s/%s' % (RESOLVER_BASE_URL, urllib.quote(identifier))
        item.content_type = resource.content_type
        item.size_in_bytes = resource.file_size

        enrich_tasks = item.enricher_task
        if isinstance(enrich_tasks, basestring):
            enrich_tasks = [item.enricher_task]

        # The enricher tasks will executed in specified order
        for task in enrich_tasks:
            # Seek to the beginning of the file before starting a task
            resource.media_file.seek(0)
            self.available_tasks[task](self.source_definition).enrich_item(item, resource.media_file)

        resource.media_file.close()

        item.db.save(item)


@celery_app.task(bind=True, base=MediaEnricher, autoretry_for=AUTORETRY_EXCEPTIONS, retry_backoff=True)
def media_enricher(self, *args, **kwargs):
    return self.start(*args, **kwargs)
