from tempfile import NamedTemporaryFile

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ocd_backend.exceptions import NotFound
from ocd_backend.log import get_source_logger
from ocd_backend.settings import USER_AGENT

log = get_source_logger('http')

RETRY_DEADLINE = 60 * 2


class CustomRetry(Retry):
    """A subclass of the Retry class but with extra logging"""

    def increment(self, method=None, url=None, response=None, error=None,
                  _pool=None, _stacktrace=None):
        res = super(CustomRetry, self).increment(method, url, response,
                                                 error, _pool, _stacktrace)
        log.info("Retrying url: %s" % url)
        return res


class FileResource:
    def __init__(self, media_file):
        self.data = None
        self.existed = None
        self.content_type = None
        self.file_size = None
        self.revision_path = None
        self.from_cache = False
        self.media_file = media_file

    def read(self):
        self.data = self.media_file.read()
        self.media_file.seek(0, 0)
        return self.data


class HttpRequestMixin:
    """A mixin that can be used by extractors that use HTTP as a method
    to fetch data from a remote source. A persistent
    :class:`requests.Session` is used to take advantage of
    HTTP Keep-Alive.
    """

    _http_session = None
    source_definition = None
    http_retries = 0

    @property
    def http_session(self, retries=3):
        """Returns a :class:`requests.Session` object. A new session is
        created if it doesn't already exist."""
        http_session = getattr(self, '_http_session', None)
        # try to get the source definition if available
        source_definition = getattr(self, 'source_definition')

        if not retries and source_definition:
            retries = source_definition.get('http_retries')

        if not http_session:
            urllib3.disable_warnings()
            session = requests.Session()
            session.headers['User-Agent'] = USER_AGENT

            http_retry = CustomRetry(total=retries, status_forcelist=[500, 503],
                                     backoff_factor=.4)
            http_adapter = HTTPAdapter(max_retries=http_retry)
            session.mount('http://', http_adapter)

            http_retry = CustomRetry(total=retries, status_forcelist=[500, 503],
                                     backoff_factor=.4)
            http_adapter = HTTPAdapter(max_retries=http_retry)
            session.mount('https://', http_adapter)

            self._http_session = session

        return self._http_session

    def fetch(self, url, path):
        return self.download_url(url)

    def download_url(self, url, partial_fetch=False):
        log.debug('Fetching item %s' % (url,))

        # hacky solution to make the timeout for certain iBabs urls longer than for other
        # providers, as big files tend to have longer response times in iBabs
        if 'ibabs.eu' in url:
            tm = 60
        else:
            tm = 15
        http_resp = self.http_session.get(url, stream=True, timeout=(3, tm), verify=False)
        http_resp.raise_for_status()

        # Create a temporary file to store the media item, write the file
        # to disk if it is larger than 1 MB.
        media_file = NamedTemporaryFile(delete=True)

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
        log.debug('Fetched item %s [%s/%s]' % (url, retrieved_bytes, content_length))

        # If the server doens't provide a content-length and this isn't
        # a partial fetch, determine the size by looking at the retrieved
        # content
        if not content_length and not partial_fetch:
            media_file.seek(0, 2)
            content_length = media_file.tell()
        if not content_length:
            content_length = 0

        media_file.seek(0, 0)

        resource = FileResource(media_file)
        resource.content_type = http_resp.headers.get('content-type')
        resource.file_size = content_length
        return resource

    def upload(self, path, data, content_type=None):
        """Upload was previously only implemented for GCSCachingMixin, the Google Cloud storage"""
        pass

class HttpRequestSimple(HttpRequestMixin):
    pass