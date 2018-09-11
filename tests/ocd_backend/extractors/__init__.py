import datetime
import glob
import os
import os.path
import shutil
from time import sleep
from unittest import TestCase

import mock
from nose.tools import raises, assert_raises
from ocd_backend.exceptions import InvalidFile
from ocd_backend.extractors import LocalCachingMixin
from ocd_backend.settings import PROJECT_PATH
from ocd_backend.utils.misc import get_sha1_hash, datetime_to_unixstamp, localize_datetime
from requests.exceptions import HTTPError


class ExtractorTestCase(TestCase):
    def setUp(self):
        self.PWD = os.path.dirname(__file__)
        dump_path = os.path.abspath(
            os.path.join(self.PWD, '..', 'test_dumps/ocd_openbeelden_test.gz')
        )
        self.source_definition = {
            'id': 'test_definition',
            'extractor': 'ocd_backend.extractors.staticfile.StaticJSONDumpExtractor',
            'transformer': 'ocd_backend.transformers.BaseTransformer',
            'item': 'ocd_backend.items.LocalDumpItem',
            'loader': 'ocd_backend.loaders.ElasticsearchLoader',
            'dump_path': dump_path,
            'index_name': 'test_index'
        }


class HTTPCachingMixinTestCase(ExtractorTestCase):
    def setUp(self):
        super(HTTPCachingMixinTestCase, self).setUp()
        self.mixin = LocalCachingMixin()
        self.mixin.source_definition = self.source_definition

        self.test_cache_path = PROJECT_PATH + "/data/cache/test_index/"

        def remove_test_cache():
            if os.path.exists(self.test_cache_path):
                shutil.rmtree(self.test_cache_path)

        self.addCleanup(remove_test_cache)

    def test_base_path(self):
        path = self.mixin.base_path('some_test_path')
        expected = self.test_cache_path + "so/me/some_test_path"
        self.assertEqual(path, expected)

    def test_write_to_cache_without_date(self):
        file_path = self.test_cache_path + "aa/bb/aabb-testfile"
        data = "test-string"
        self.mixin._write_to_cache(file_path, data)
        expected_modified_date = localize_datetime(datetime.datetime.now())
        file_exists = os.path.exists("%s-%i" % (file_path, datetime_to_unixstamp(expected_modified_date)))
        self.assertTrue(file_exists, True)

    def test_write_to_cache_with_date(self):
        file_path = self.test_cache_path + "aa/bb/aabb-testfile"
        data = "test-string"
        modified_date = datetime.datetime(2018, 11, 30, 12, 0)
        self.mixin._write_to_cache(file_path, data, modified_date)
        file_exists = os.path.exists(file_path + "-1543575600")
        self.assertTrue(file_exists, True)

    def test_write_to_cache_path_exists(self):
        path = self.test_cache_path + "aa/bb/"
        os.makedirs(path)

        data = "test-string"

        try:
            self.mixin._write_to_cache(path + 'aabb-testfile', data)
        except:
            self.fail("Unexpected exception caught")

    def test_write_to_cache_permission_denied(self):
        path = self.test_cache_path + "aa/bb/"
        os.makedirs(path)

        # Make path unwriteable
        os.chmod(path, 0555)

        data = "test-string"

        try:
            self.mixin._write_to_cache(path + 'aabb-testfile', data)
        except IOError:
            pass
        else:
            self.fail("Unexpected exception caught")
        finally:
            # Reset permissions
            os.chmod(path, 0775)

    @mock.patch('tests.ocd_backend.glob.glob')
    def test_latest_version_path(self, mocked_glob):
        mocked_glob.return_value = [
            'bf6af22c3383fca48c210b9272d76cd8f45ce532-1526575691',
            'bf6af22c3383fca48c210b9272d76cd8f45ce532-1526575908',
            'bf6af22c3383fca48c210b9272d76cd8f45ce532-1526575729',
            'bf6af22c3383fca48c210b9272d76cd8f45ce532-1526575551',
        ]
        result = '%s-%s' % self.mixin._latest_version("bf6af22c3383fca48c210b9272d76cd8f45ce532")
        self.assertEqual(result, "bf6af22c3383fca48c210b9272d76cd8f45ce532-1526575908")

    @mock.patch.object(LocalCachingMixin, 'download_url')
    def test_modified_data_source(self, mocked_download_url):
        with open(os.path.join(self.PWD, "..", "test_dumps/notubiz_meeting_amsterdam.json"), 'rb') as f:
            data1 = f.read()

        with open(os.path.join(self.PWD, "..", "test_dumps/notubiz_meeting_amsterdam_update1.json"), 'rb') as f:
            data2 = f.read()

        # The second and third call to _download_file will return the second data source
        mocked_download_url.side_effect = [
            (data1, 'application/json',),
            (data2, 'application/json',),
            (data2, 'application/json',),
        ]

        # The download will be mocked so this is just for show
        url = "https://api.notubiz.nl/events/meetings/458902?format=json&version=1.10.8"
        self.mixin.fetch(url, datetime.datetime(2018, 11, 30, 12, 0))
        sleep(1)
        self.mixin.fetch(url, datetime.datetime(2018, 11, 30, 12, 1))
        sleep(1)
        self.mixin.fetch(url, datetime.datetime(2018, 11, 30, 12, 1))

        url_hash = get_sha1_hash(url)
        base_path = self.mixin.base_path(url_hash)

        file_count = len(glob.glob(base_path + "*"))
        self.assertEqual(file_count, 2)

    @mock.patch.object(LocalCachingMixin, 'download_url')
    def test_fetch_failed_download(self, mocked_download_url):
        mocked_download_url.side_effect = HTTPError
        with self.assertRaises(HTTPError):
            self.mixin.fetch("http://example.com/some/not/existing/url", datetime.datetime(2018, 11, 30, 12, 0))

    def test_check_path_file(self):
        path = self.test_cache_path + "ab/ab/"

        os.makedirs(path)
        with open(os.path.join(self.test_cache_path + "ab/ab/small_file"), 'w') as f:
            f.write("{}")

        try:
            self.mixin._check_path(self.test_cache_path + "ab/ab/small_file")
        except InvalidFile:
            self.fail("Unexpected exception InvalidFile caught")

    def test_check_path_file_too_small(self):
        path = self.test_cache_path + "ab/ab/"

        os.makedirs(path)
        with open(os.path.join(self.test_cache_path + "ab/ab/small_file"), 'w') as f:
            f.write("{")

        with self.assertRaises(InvalidFile):
            self.mixin._check_path(self.test_cache_path + "ab/ab/small_file")


# Import test modules here so the noserunner can pick them up, and the
# ExtractorTestCase is parsed. Add additional testcases when required
from .staticfile import (
    StaticfileExtractorTestCase, StaticJSONExtractorTestCase
)
