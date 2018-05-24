import glob
import os
from datetime import datetime

import requests
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from ocd_backend.exceptions import InvalidFile
from ocd_backend.log import get_source_logger
from ocd_backend.settings import USER_AGENT, DATA_DIR_PATH
from ocd_backend.utils.misc import get_sha1_hash, get_sha1_file_hash, localize_datetime, datetime_to_unixstamp

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

    def interval_generator(self):
        """Returns a generator with date intervals

        The intervals are generated between the 'start_date' and 'end_date'
        specified in the source configuration. The default is one month ago
        from now, which can be changed by specifying 'months_interval'.
        """

        months = 1  # Max 1 months intervals by default
        if 'months_interval' in self.source_definition:
            months = self.source_definition['months_interval']
        days = (months / 2.0) * 30

        if (months / 2.0) < 1.0:
            interval_delta = relativedelta(days=days)
        else:
            interval_delta = relativedelta(months=months)

        current_start = datetime.today() - interval_delta

        if 'start_date' in self.source_definition:
            current_start = parse(self.source_definition['start_date'])

        end_date = datetime.today() + interval_delta

        if 'end_date' in self.source_definition:
            end_date = parse(self.source_definition['end_date'])

        while True:
            current_end = current_start + interval_delta

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
            requests.packages.urllib3.disable_warnings()
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


class HTTPCachingMixin(BaseExtractor, HttpRequestMixin):
    def run(self):
        raise NotImplementedError

    def is_modified(self):
        # raise NotImplementedError
        return True

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
    def latest_version_path(file_path):
        version_paths = glob.glob('%s-*' % file_path)

        if len(version_paths) < 1:
            raise OSError

        versions = [os.path.basename(version_path).rpartition("-")[2] for version_path in version_paths]
        latest_version = sorted(versions, reverse=True)[0]

        return '%s-%s' % (file_path, latest_version)

    @staticmethod
    def _check_path(path):
        file_bytes = os.path.getsize(path)

        # Raise OSError if the filesize is smaller than two bytes
        if file_bytes < 2:
            raise InvalidFile

    def fetch(self, url):
        url_hash = get_sha1_hash(url)
        base_path = self.base_path(url_hash)

        try:
            latest_version_path = self.latest_version_path(base_path)
            self._check_path(latest_version_path)
        except OSError:
            # File does not exist, download and cache the url
            download_data = self._download_file(url)
            self._write_to_cache(base_path, download_data)
            return download_data

        # Do smart test to see if newer
        if not self.is_modified():
            return

        # Download file and cache it if the hash differs
        download_data = self._download_file(url)
        if not self._hash_match(download_data, latest_version_path):
            self._write_to_cache(base_path, download_data)

        # todo force_old_files
        return download_data

    @staticmethod
    def _hash_match(new_data, file_path):
        new_hash = get_sha1_hash(new_data)
        old_hash = get_sha1_file_hash(file_path)

        # When the hashes are the same return False
        if new_hash == old_hash:
            return True

        return False

    def _download_file(self, url):
        resp = self.http_session.get(url)
        resp.raise_for_status()
        return resp.content

    @staticmethod
    def _write_to_cache(file_path, data, modified_date=None):
        try:
            # Create all subdirectories
            os.makedirs(os.path.dirname(file_path))
        except OSError:
            # Let's assume the directory exists
            pass

        if not modified_date:
            modified_date = datetime.now()

        modified_date = datetime_to_unixstamp(localize_datetime(modified_date))

        with open('%s-%s' % (file_path, modified_date), 'w') as f:
            f.write(data)
