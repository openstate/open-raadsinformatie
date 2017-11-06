import os
from hashlib import sha1

from ocd_backend.enrichers.media_enricher import MediaEnricher
from ocd_backend.log import get_source_logger
from ocd_backend.settings import DATA_DIR_PATH

log = get_source_logger('enricher')


class StaticMediaEnricher(MediaEnricher):
    def fetch_media(self, object_id, url, partial_fetch=False):
        http_resp = self.http_session.get(url, stream=True, timeout=(60, 120))
        http_resp.raise_for_status()

        static_dir = os.path.join(DATA_DIR_PATH, 'static')

        if not os.path.exists(static_dir):
            log.info('Creating static directory %s' % static_dir)
            os.makedirs(static_dir)

        file_id = sha1(url).hexdigest()

        # Create a file to store the media item in the static dir
        media_file = open(os.path.join(static_dir, file_id), "w+b")

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

        log.debug('Fetched media item %s [%s/%s]' % (
            url, retrieved_bytes, content_length))

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
