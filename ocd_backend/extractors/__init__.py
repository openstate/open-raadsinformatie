import cStringIO
import errno
import glob
import gzip
import os
from datetime import datetime

import requests
import urllib3
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from google.cloud import storage, exceptions
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ocd_backend.exceptions import InvalidFile
from ocd_backend.log import get_source_logger
from ocd_backend.settings import USER_AGENT, DATA_DIR_PATH
from ocd_backend.utils.misc import get_sha1_hash, localize_datetime, datetime_to_unixstamp, \
    str_to_datetime

log = get_source_logger('extractor')


class BaseExtractor(object):
    """The base class that other extractors should inherit."""

    def __init__(self, source_definition):
        """
        :param source_definition: The configuration of a single source in
            the form of a dictionary (as defined in the settings).
        :type source_definition: dict.
        """
        self.source_definition = source_definition

    def run(self):
        """Starts the extraction process.

        This method must be implemented by the class that inherits the
        :py:class:`BaseExtractor` and should return a generator that
        yields one item per value. Items should be formatted as tuples
        containing the following elements (in this order):

        - the content-type of the data retrieved from the source (e.g.
          ``application/json``)
        - the data in it's original format, as retrieved from the source
          (as a string)
        """
        raise NotImplementedError

    def _interval_delta(self):
        """Returns a datetime delta.

        This method uses 'months_interval' specified in the source
        configuration, whichs defaults to 1 month. If the 'months_interval'
        is smaller than 2, the delta is split in two. Therefore, such
        intervals are measured in days instead of months.
        """
        months = 1  # Max 1 months intervals by default
        if 'months_interval' in self.source_definition:
            months = self.source_definition['months_interval']

        if (months / 2.0) < 1.0:
            days = (months / 2.0) * 30
            return relativedelta(days=days)

        return relativedelta(months=months)

    def date_interval(self):
        """Returns a tuple of a start_date and end_date

        The interval are exactly the 'start_date' and 'end_date' specified
        in the source configuration. If one or both is not specified, the
        date will be the date of today with an offset calculated by
        :py:meth:`BaseExtractor._interval_delta`.

        :return: A start_date and end_date tuple
        :rtype: tuple
        """
        interval_delta = self._interval_delta()

        start_date = datetime.today() - interval_delta

        if 'start_date' in self.source_definition:
            start_date = parse(self.source_definition['start_date'])

        end_date = datetime.today() + interval_delta

        if 'end_date' in self.source_definition:
            end_date = parse(self.source_definition['end_date'])

        return start_date, end_date

    def interval_generator(self):
        """Returns a generator with date intervals

        The intervals are generated between the 'start_date' and 'end_date'
        specified in the source configuration. If one or both is not specified, the
        date will be the date of today with an offset calculated by
        :py:meth:`BaseExtractor._interval_delta`.

        :return: A generator yielding a start_date and end_date for each
        interval
        :rtype: generator
        """

        current_start, end_date = self.date_interval()

        while True:
            current_end = current_start + self._interval_delta()

            # If next current_end exceeds end_date then stop at end_date
            if current_end > end_date:
                current_end = end_date
                log.debug("Next interval exceeds %s, months_interval not used"
                          % end_date)

            yield current_start, current_end

            current_start = current_end + relativedelta(seconds=1)

            # Stop while loop if exceeded end_date
            if current_start > end_date:
                break


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

    @property
    def http_session(self):
        """Returns a :class:`requests.Session` object. A new session is
        created if it doesn't already exist."""
        http_session = getattr(self, '_http_session', None)
        # try to get the source definition if available
        source_definition = getattr(self, 'source_definition', {})
        total_retries = source_definition.get('http_retries', 0)
        if not http_session:
            urllib3.disable_warnings()
            session = requests.Session()
            session.headers['User-Agent'] = USER_AGENT

            http_retry = CustomRetry(total=total_retries, status_forcelist=[500, 503],
                                     backoff_factor=.4)
            http_adapter = HTTPAdapter(max_retries=http_retry)
            session.mount('http://', http_adapter)

            http_retry = CustomRetry(total=total_retries, status_forcelist=[500, 503],
                                     backoff_factor=.4)
            http_adapter = HTTPAdapter(max_retries=http_retry)
            session.mount('https://', http_adapter)

            self._http_session = session

        return self._http_session


class LocalCachingMixin(HttpRequestMixin):
    source_definition = None

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

    def fetch(self, url, modified_date):
        modified_date = localize_datetime(str_to_datetime(modified_date))

        url_hash = get_sha1_hash(url)
        base_path = self.base_path(url_hash)

        try:
            file_path, latest_version = self._latest_version(base_path)
            latest_version_path = '%s-%s' % (file_path, latest_version)
            self._check_path(latest_version_path)
        except OSError:
            # File does not exist, download and cache the url
            data, _ = self._download_file(url)
            self._write_to_cache(base_path, data, modified_date)
            return data

        if modified_date and modified_date > str_to_datetime(latest_version):
            # If file has been modified download it
            data, _ = self._download_file(url)
            self._write_to_cache(base_path, data, modified_date)
            return data
        else:
            # todo force_old_files
            with open(latest_version_path, 'rb') as f:
                return f.read()

    def _download_file(self, url):
        resp = self.http_session.get(url)
        resp.raise_for_status()
        return resp.content, resp.headers['Content-Type']

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


class GCSCachingMixin(LocalCachingMixin):
    """Google Cloud Storage caching mixin.
    """

    storage_client = storage.Client()
    bucket_name = None
    _bucket = None

    def get_bucket(self):
        if self._bucket:
            return self._bucket

        if not self.bucket_name:
            raise Exception("The 'bucket_name' needs to be set.")

        try:
            self._bucket = self.storage_client.get_bucket(self.bucket_name)
        except exceptions.NotFound:
            storage.Bucket(
                self.storage_client,
                name=self.bucket_name
            ).create(location='europe-west4')
            self._bucket = self.storage_client.get_bucket(self.bucket_name)

        return self._bucket

    def fetch(self, url, path, modified_date=None):
        bucket = self.get_bucket()
        blob = bucket.get_blob(path)
        if not blob:
            blob = bucket.blob(path)

            # File does not exist
            data, content_type = self._download_file(url)
            self.compressed_upload(blob, data, content_type)
            return data

        modified_date = localize_datetime(str_to_datetime(modified_date))
        if modified_date > blob.updated:
            # Uploading newer file
            data, content_type = self._download_file(url)
            self.compressed_upload(blob, data, content_type)
            return data
        elif self.source_definition['force_old_files']:
            # Downloading up-to-date file
            return blob.download_as_string()

    @staticmethod
    def compressed_upload(blob, data, content_type):
        f = cStringIO.StringIO()

        with gzip.GzipFile(filename='', mode='wb', fileobj=f) as gf:
            gf.write(data)

        blob.content_encoding = 'gzip'
        blob.upload_from_file(f, rewind=True, content_type=content_type)
