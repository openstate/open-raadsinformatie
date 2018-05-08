import os
from base64 import b64encode
from tempfile import SpooledTemporaryFile

from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from ocd_backend.enrichers import BaseEnricher
from ocd_backend.enrichers.media_enricher.tasks import ImageMetadata, \
    MediaType, FileToText
from ocd_backend.enrichers.media_enricher.tasks.ggm import \
    GegevensmagazijnMotionText
from ocd_backend.exceptions import UnsupportedContentType
from ocd_backend.log import get_source_logger
from ocd_backend.settings import TEMP_DIR_PATH, USER_AGENT, RESOLVER_BASE_URL
from ocd_backend.utils.misc import get_secret, get_sha1_hash

log = get_source_logger('enricher')


class MediaEnricher(BaseEnricher):
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

    http_session = None

    def setup_http_session(self):
        if self.http_session:
            self.http_session.close()

        self.http_session = Session()
        self.http_session.headers['User-Agent'] = USER_AGENT

        http_retry = Retry(total=5, status_forcelist=[500, 503],
                           backoff_factor=.5)
        http_adapter = HTTPAdapter(max_retries=http_retry)
        self.http_session.mount('http://', http_adapter)

        http_retry = Retry(total=5, status_forcelist=[500, 503],
                           backoff_factor=.5)
        http_adapter = HTTPAdapter(max_retries=http_retry)
        self.http_session.mount('https://', http_adapter)

    def setup_http_auth(self):
        user, password = get_secret(self.source_definition['id'])
        self.http_session.headers['Authorization'] = 'Basic %s' % b64encode(
            '%s:%s' % (user, password))

    def fetch_media(self, object_id, url, partial_fetch=False):
        """Retrieves a given media object from a remote (HTTP) location
        and returns the content-type and a file-like object containing
        the media content.

        The file-like object is a temporary file that - depending on the
        size - lives in memory or on disk. Once the file is closed, the
        contents are removed from storage.

        :param object_id: the identifier of the item that is being enriched.
        :type object_id: str
        :param url: the URL of the media asset.
        :type url: str.
        :param partial_fetch: determines if the the complete file should
            be fetched, or if only the first 2 MB should be retrieved.
            This feature is used to prevent complete retrieval of large
            a/v material.
        :type partial_fetch: bool.
        :returns: a tuple with the ``content-type``, ``content-lenght``
            and a file-like object containing the media content. The
            value of ``content-length`` will be ``None`` in case
            a partial fetch is requested and ``content-length`` is not
            returned by the remote server.
        """

        http_resp = self.http_session.get(url, stream=True, timeout=(60, 120))
        http_resp.raise_for_status()

        if not os.path.exists(TEMP_DIR_PATH):
            log.debug('Creating temp directory %s' % TEMP_DIR_PATH)
            os.makedirs(TEMP_DIR_PATH)

        # Create a temporary file to store the media item, write the file
        # to disk if it is larger than 1 MB.
        media_file = SpooledTemporaryFile(max_size=1024 * 1024, prefix='ocd_m_',
                                          suffix='.tmp',
                                          dir=TEMP_DIR_PATH)

        # When a partial fetch is requested, request up to two MB
        partial_target_size = 1024 * 1024 * 2
        content_length = http_resp.headers.get('content-length')
        if content_length and int(content_length) < partial_target_size:
            partial_target_size = int(content_length)

        retrieved_bytes = 0
        for chunk in http_resp.iter_content(chunk_size=512 * 1024):
            if chunk:  # filter out keep-alive chunks
                media_file.write(chunk)
                retrieved_bytes += len(chunk)

            if partial_fetch and retrieved_bytes >= partial_target_size:
                break

        media_file.flush()
        log.debug('Fetched media item %s [%s/%s]' % (url, retrieved_bytes,
                                                     content_length))

        # If the server doens't provide a content-length and this isn't
        # a partial fetch, determine the size by looking at the retrieved
        # content
        if not content_length and not partial_fetch:
            media_file.seek(0, 2)
            content_length = media_file.tell()

        return (
            http_resp.headers.get('content-type'),
            content_length,
            media_file
        )

    def enrich_item(self, item):
        """Enriches the media objects referenced in a single item.

        First, a media item will be retrieved from the source, than the
        registered and configured tasks will run. In case fetching the
        item fails, enrichment of the media item will be skipped. In case
        a specific media enrichment task fails, only that task is
        skipped, which means that we move on to the next task.
        """
        self.setup_http_session()

        if self.enricher_settings.get('authentication', False):
            self.setup_http_auth()

        # Check the settings to see if media should by fetch partially
        partial_fetch = self.enricher_settings.get('partial_media_fetch', False)

        content_type, content_length, media_file = self.fetch_media(
            item.get_ori_id(),
            item.original_url,
            partial_fetch
        )

        item.url = '%s/%s' % (RESOLVER_BASE_URL, get_sha1_hash(item.original_url))
        item.content_type = content_type
        item.size_in_bytes = content_length

        enrich_tasks = item.Meta.enricher_task
        if isinstance(enrich_tasks, basestring):
            enrich_tasks = [item.Meta.enricher_task]

        for task in enrich_tasks:
            # Seek to the beginning of the file before starting a task
            media_file.seek(0)
            try:
                self.available_tasks[task](item, content_type, media_file)
            except UnsupportedContentType:
                log.info('Skipping media enrichment task %s, '
                         'content-type %s (object_id: %s, url %s) is not '
                         'supported.' % (task, content_type, item.get_ori_id(),
                                         item.original_url))
                continue

            media_file.close()

        item.save()
