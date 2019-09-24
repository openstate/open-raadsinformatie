import requests

from ocd_backend.app import celery_app
from ocd_backend.enrichers import BaseEnricher
from ocd_backend.enrichers.media_enricher.tasks import ImageMetadata, \
    MediaType, FileToText
from ocd_backend.enrichers.media_enricher.tasks.ggm import \
    GegevensmagazijnMotionText
from ocd_backend.exceptions import UnsupportedContentType, SkipEnrichment
from ocd_backend.log import get_source_logger
from ocd_backend.settings import RESOLVER_BASE_URL, AUTORETRY_EXCEPTIONS
from ocd_backend.utils.http import HttpRequestMixin
from ocd_backend.utils.misc import strip_scheme

log = get_source_logger('enricher')


class MediaEnricher(BaseEnricher, HttpRequestMixin):
    """An enricher that is responsible for enriching external media
    (images, audio, video, etc.) referenced in items (in the
    ``media_urls`` array).

    Media items are fetched from the source and then passed on to a
    set of registered tasks that are responsible for the analysis.
    """

    #: The registry of available sub-tasks that are responsible for the
    #: analysis of media items. Which tasks are executed depends on a
    #: combination of the configuration in ``sources.json`` and the
    #: returned ``content-type``.
    available_tasks = {
        'image_metadata': ImageMetadata,
        'media_type': MediaType,
        'file_to_text': FileToText,
        'ggm_motion_text': GegevensmagazijnMotionText
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
            content_type, content_length, media_file = self.fetch(
                item.original_url,
                identifier,
                date_modified,
            )
        except requests.HTTPError as e:
            raise SkipEnrichment(e)

        item.url = '%s/%s' % (RESOLVER_BASE_URL, identifier)
        item.content_type = content_type
        item.size_in_bytes = content_length

        enrich_tasks = item.enricher_task
        if isinstance(enrich_tasks, basestring):
            enrich_tasks = [item.enricher_task]

        for task in enrich_tasks:
            # Seek to the beginning of the file before starting a task
            media_file.seek(0)
            try:
                self.available_tasks[task](item, content_type, media_file)
            except UnsupportedContentType:
                log.info('Skipping media enrichment task %s, '
                         'content-type %s (object_id: %s, url %s) is not '
                         'supported.' % (task, content_type, item.get_ori_identifier(),
                                         item.original_url))
                continue

        media_file.close()

        item.db.save(item)


@celery_app.task(bind=True, base=MediaEnricher, autoretry_for=AUTORETRY_EXCEPTIONS, retry_backoff=True)
def media_enricher(self, *args, **kwargs):
    return self.start(*args, **kwargs)
