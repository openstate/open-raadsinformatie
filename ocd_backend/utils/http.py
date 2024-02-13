import base64
import io
import gzip
import hashlib
from tempfile import NamedTemporaryFile

import requests
import urllib3
from google.api_core import retry
from google.auth.exceptions import GoogleAuthError
from google.cloud import storage, exceptions
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
        http_resp = self.http_session.get(url, stream=True, timeout=(3, 5), verify=False)
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

        media_file.seek(0, 0)

        resource = FileResource(media_file)
        resource.content_type = http_resp.headers.get('content-type')
        resource.file_size = content_length
        return resource

    def upload(self, path, data, content_type=None):
        """Upload is only implemented for GCSCachingMixin"""
        pass


class GCSCachingMixin(HttpRequestMixin):
    """Google Cloud Storage caching mixin.

    Fetch resources from a remote source while adding the data to Google Cloud
    Storage for caching purposes. When the resource has not changed, this
    mixin will serve from cache instead of doing a new request.
    """
    try:
        storage_client = storage.Client()
    except GoogleAuthError as e:
        log.warning(f'GCSCachingMixin: storage client authentication failed, using HttpRequestMixin instead: {str(e)}')
        storage_client = False

    bucket_name = None
    default_content_type = None
    _bucket = None

    @classmethod
    def factory(cls, bucket_name):
        ins = cls()
        ins.bucket_name = bucket_name
        return ins

    def get_bucket(self):
        """Get the bucket defined by 'bucket_name' from the storage_client.
        Throws a ValueError when bucket_name is not set. If the bucket does not
        exist in GCS, a new bucket will be created.
        """
        if self._bucket:
            return self._bucket

        if not self.bucket_name:
            raise ValueError("The 'bucket_name' needs to be set.")

        try:
            self._bucket = self.storage_client.get_bucket(self.bucket_name)
        except (exceptions.NotFound, exceptions.Forbidden):
            bucket = storage.Bucket(self.storage_client, name=self.bucket_name)
            bucket.versioning_enabled = True
            bucket.lifecycle_rules = [{
                'action': {'type': 'SetStorageClass', 'storageClass': 'NEARLINE'},
                'condition': {
                    'numNewerVersions': 1,
                    'matchesStorageClass': ['REGIONAL', 'STANDARD'],
                    'age': 30
                }
            }]
            try:
                bucket.create(location='europe-west4')
            except exceptions.Conflict:
                raise
            self._bucket = self.storage_client.get_bucket(self.bucket_name)

        return self._bucket

    def fetch(self, url, path, condition=None):
        """Fetch a resource url and save it to a path in GCS. The resource will
        only be actually downloaded from the source when the cached file does
        not exist, otherwise the file will be downloaded from cache unless
        'force_old_files' has been set.
        """

        # If the storage_client has not been loaded fall back to HttpRequestMixin fetch
        if not self.storage_client:
            return super(GCSCachingMixin, self).fetch(url, path)

        bucket = self.get_bucket()
        blob = self.exists(path)

        try:
            force_old_files = self.source_definition['force_old_files']
        except (TypeError, KeyError):
            force_old_files = getattr(self, 'force_old_files', False)

        # try:
        #     skip_old_files = self.source_definition['skip_old_files']
        # except (TypeError, KeyError):
        #     skip_old_files = getattr(self, 'skip_old_files', False)

        if not blob or force_old_files:
            # File does not exist in the cache or we want to ignore the cache with force_old_files
            resource = self.download_url(url)
            resource.existed = bool(blob)

            blob = bucket.blob(path)
            revision_path = self.upload_blob(blob, resource.read(), resource.content_type)
            log.debug('Uploaded file to GCS bucket %s: %s' % (self.bucket_name, revision_path))

            resource.revision_path = revision_path
            return resource
        else:
            resource = self.download_cache(path)
            resource.from_cache = True
            return resource

    def upload(self, path, data, content_type=None):
        """Save data to a path in GCS. The content_type can be specified, or
        will default to default_content_type.
        """

        # If the storage_client has not been loaded fall back to HttpRequestMixin save
        if not self.storage_client:
            return super(GCSCachingMixin, self).upload(path, data, content_type)

        bucket = self.get_bucket()
        blob = bucket.blob(path)

        return self.upload_blob(blob, data, content_type)

    def upload_blob(self, blob, data, content_type=None, skip_exists=True):
        """Upload a gzip compressed file to a GCS blob. If content_type is
        empty, the default_content_type will be used. If both are empty a
        ValueError will be raised. It returns the path with revision generation.
        """
        assert blob, "blob must not be None"
        assert data, "data must not be None"

        f = io.BytesIO()

        with gzip.GzipFile(filename='', mode='wb', fileobj=f) as gf:
            if isinstance(data, str):
                data = data.encode('utf-8')
            gf.write(data)

        if skip_exists:
            md5_hash = base64.b64encode(hashlib.md5(f.read()).digest())
            f.seek(0, 0)

            if blob.md5_hash == md5_hash:
                assert blob.generation
                revision_path = '{}/{}#{}'.format(blob.bucket.name, blob.name, blob.generation)
                log.debug('Hash match before upload, skipping: %s' % revision_path)
                return revision_path

        blob.content_encoding = 'gzip'
        self._do_upload(f, blob, rewind=True, content_type=content_type)
        return '{}/{}#{}'.format(blob.bucket.name, blob.name, blob.generation)

    @retry.Retry(deadline=RETRY_DEADLINE)
    def _do_upload(self, f, blob, *args, **kwargs):
        """Do the actual uploading. This action will retry using exponential
        back-off if it is raises an transient API error.
        """
        return blob.upload_from_file(f, *args, **kwargs)

    def download_cache(self, path):
        """Retrieve and return the cached file"""
        bucket = self.get_bucket()
        blob = bucket.get_blob(path)

        if not blob:
            raise NotFound(path)

        media_file = io.BytesIO()
        self._do_download(blob, media_file)
        media_file.seek(0, 0)
        log.debug('Retrieved file from GCS bucket %s: %s' % (self.bucket_name, path))

        resource = FileResource(media_file)
        resource.content_type = blob.content_type
        resource.file_size = blob.size
        return resource

    @retry.Retry(deadline=RETRY_DEADLINE)
    def _do_download(self, blob, media_file):
        """Do the actual downloading. This action will retry using exponential
        back-off if it is raises an transient API error.
        """
        return blob.download_to_file(media_file)

    @retry.Retry(deadline=RETRY_DEADLINE)
    def exists(self, path):
        """Check if path exists and returns the blob. This action will retry
        using exponential back-off if it is raises an transient API error.
        """
        if self.storage_client:
            bucket = self.get_bucket()
            return bucket.get_blob(path)
        else:
            return False
