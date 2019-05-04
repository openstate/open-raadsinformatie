import base64
import cStringIO
import errno
import glob
import gzip
import os
from datetime import datetime
from tempfile import NamedTemporaryFile

import requests
import urllib3
from google.auth.exceptions import GoogleAuthError
from google.cloud import storage, exceptions
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ocd_backend.exceptions import InvalidFile, ItemAlreadyProcessed
from ocd_backend.log import get_source_logger
from ocd_backend.settings import TEMP_DIR_PATH
from ocd_backend.settings import USER_AGENT, DATA_DIR_PATH
from ocd_backend.utils.misc import localize_datetime, datetime_to_unixstamp, \
    str_to_datetime

log = get_source_logger('http')


class CustomRetry(Retry):
    """A subclass of the Retry class but with extra logging"""

    def increment(self, method=None, url=None, response=None, error=None,
                  _pool=None, _stacktrace=None):
        res = super(CustomRetry, self).increment(method, url, response,
                                                 error, _pool, _stacktrace)
        log.info("Retrying url: %s" % url)
        return res


class HttpRequestMixin(object):
    """A mixin that can be used by extractors that use HTTP as a method
    to fetch data from a remote source. A persistent
    :class:`requests.Session` is used to take advantage of
    HTTP Keep-Alive.
    """

    _http_session = None
    source_definition = None

    @property
    def http_session(self, retries=None):
        """Returns a :class:`requests.Session` object. A new session is
        created if it doesn't already exist."""
        http_session = getattr(self, '_http_session', None)
        # try to get the source definition if available
        source_definition = getattr(self, 'source_definition', {})

        if not retries:
            retries = source_definition.get('http_retries', 0)

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

    def fetch(self, url, path, modified_date):
        return self.download_url(url)

    def fetch_data(self, url, path, modified_date):
        _, _, media_file = self.fetch(url, path, modified_date)
        return media_file.read()

    def download_url(self, url, partial_fetch=False):
        http_resp = self.http_session.get(url, stream=True, timeout=(60, 120))
        http_resp.raise_for_status()

        if not os.path.exists(TEMP_DIR_PATH):
            log.debug('Creating temp directory %s' % TEMP_DIR_PATH)
            os.makedirs(TEMP_DIR_PATH)

        # Create a temporary file to store the media item, write the file
        # to disk if it is larger than 1 MB.
        media_file = NamedTemporaryFile(dir=TEMP_DIR_PATH)

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

        return (
            http_resp.headers.get('content-type'),
            content_length,
            media_file
        )


class LocalCachingMixin(HttpRequestMixin):

    def base_path(self, file_name):
        first_dir = file_name[0:2]
        second_dir = file_name[2:4]

        return os.path.join(
            DATA_DIR_PATH,
            'cache',
            self.source_definition['index_name'],
            first_dir,
            second_dir,
            file_name,
        )

    @staticmethod
    def _latest_version(file_path):
        version_paths = glob.glob('%s-*' % file_path)

        if len(version_paths) < 1:
            raise OSError

        versions = [os.path.basename(version_path).rpartition("-")[2] for version_path in version_paths]
        latest_version = sorted(versions, reverse=True)[0]

        return file_path, latest_version,

    @staticmethod
    def _check_path(path):
        file_bytes = os.path.getsize(path)

        # Raise OSError if the filesize is smaller than two bytes
        if file_bytes < 2:
            raise InvalidFile

    def fetch(self, url, path, modified_date):
        modified_date = localize_datetime(str_to_datetime(modified_date))

        url_hash = base64.urlsafe_b64encode(path)
        base_path = self.base_path(url_hash)

        try:
            file_path, latest_version = self._latest_version(base_path)
            latest_version_path = '%s-%s' % (file_path, latest_version)
            self._check_path(latest_version_path)
        except OSError:
            # File does not exist, download and cache the url
            content_type, content_length, media_file = self.download_url(url)
            data = media_file.read()
            # read() iterates over the file to the end, so we have to seek to the beginning to use it again!
            media_file.seek(0, 0)
            self._write_to_cache(base_path, data, modified_date)
            return content_type, content_length, media_file

        if modified_date and modified_date > str_to_datetime(latest_version):
            # If file has been modified download it
            content_type, content_length, media_file = self.download_url(url)
            data = media_file.read()
            media_file.seek(0, 0)
            self._write_to_cache(base_path, data, modified_date)
            return content_type, content_length, media_file
        else:
            if self.source_definition.get('force_old_files'):
                with open(latest_version_path, 'rb') as f:
                    f.seek(0, 2)
                    content_length = f.tell()
                    f.seek(0, 0)
                    return None, content_length, f.read()

        raise ItemAlreadyProcessed("Item %s has already been processed on %s. "
                                   "Set 'force_old_files' in source_definition "
                                   "to download old files from cache." %
                                   (url, latest_version))

    @staticmethod
    def _write_to_cache(file_path, data, modified_date=None):
        try:
            # Create all subdirectories
            os.makedirs(os.path.dirname(file_path))
        except OSError, e:
            # Reraise if error is not 'File exists'
            if e.errno != errno.EEXIST:
                raise e

        if not modified_date:
            modified_date = datetime.now()

        modified_date = datetime_to_unixstamp(localize_datetime(modified_date))

        with open('%s-%s' % (file_path, modified_date), 'w') as f:
            f.write(data)


class GCSCachingMixin(HttpRequestMixin):
    """Google Cloud Storage caching mixin.

    Fetch resources from a remote source while adding the data to Google Cloud
    Storage for caching purposes. When the resource has not changed, this
    mixin will serve from cache instead of doing a new request.
    """
    try:
        storage_client = storage.Client()
    except GoogleAuthError as e:
        log.warning('GCSCachingMixin: storage client failed, using HttpRequestMixin instead. %s', e)
        storage_client = False

    bucket_name = None
    default_content_type = None
    _bucket = None

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

    def fetch(self, url, path, modified_date):
        """Fetch a resource url and save it to a path in GCS. The resource will
        only be downloaded from the source when the file has been modified,
        otherwise the file will be downloaded from cache unless 'force_old_files'
        has been set.
        """

        # If the storage_client has not been loaded fall back to HttpRequestMixin fetch
        if not self.storage_client:
            return super(GCSCachingMixin, self).fetch(url, path, modified_date)

        bucket = self.get_bucket()
        blob = bucket.get_blob(path)

        if not blob or self.source_definition.get('force_old_files'):
            # File does not exist in the cache or we want to ignore the cache with force_old_files
            blob = bucket.blob(path)
            content_type, content_length, media_file = self.download_url(url)
            data = media_file.read()
            # read() iterates over the file to the end, so we have to seek to the beginning to use it again!
            media_file.seek(0, 0)
            self.compressed_upload(blob, data, content_type)
            log.debug('Uploaded file %s to cache' % path)
            return content_type, content_length, media_file
        else:
            # Retrieve and return the cached file
            media_file = cStringIO.StringIO()
            blob.download_to_file(media_file)
            media_file.seek(0, 0)
            log.debug('Retrieved file %s from cache' % path)
            return blob.content_type, blob.size, media_file

    def save(self, path, data, content_type=None):
        """Save data to a path in GCS. The content_type can be specified, or
        will default to default_content_type.
        """

        bucket = self.get_bucket()
        blob = bucket.get_blob(path)
        self.compressed_upload(blob, data, content_type)

    def compressed_upload(self, blob, data, content_type=None):
        """Upload a gzip compressed file to GCS. If content_type is empty, the
        default_content_type will be used. If both are empty a ValueError will
        be raised.
        """

        if not content_type:
            if self.default_content_type:
                content_type = self.default_content_type
            else:
                raise ValueError("No 'content_type' or 'default_content_type' "
                                 "specified")

        f = cStringIO.StringIO()

        with gzip.GzipFile(filename='', mode='wb', fileobj=f) as gf:
            gf.write(data)

        blob.content_encoding = 'gzip'
        blob.upload_from_file(f, rewind=True, content_type=content_type)
