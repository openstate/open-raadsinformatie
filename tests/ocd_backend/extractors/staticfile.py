import gzip
import json

from ocd_backend.exceptions import ConfigurationError
from ocd_backend.extractors.staticfile import (
    StaticJSONDumpExtractor, StaticJSONExtractor
)
from . import ExtractorTestCase


class StaticfileExtractorTestCase(ExtractorTestCase):
    def setUp(self):
        super(StaticfileExtractorTestCase, self).setUp()
        self.extractor = StaticJSONDumpExtractor(self.source_definition)

    def test_dump_path_set(self):
        self.assertIn('dump_path', self.source_definition)

    def test_no_dump_path_set(self):
        source_def = self.source_definition
        source_def.pop('dump_path')
        with self.assertRaises(ConfigurationError) as cm:
            StaticJSONDumpExtractor(self.source_definition)

    def test_load_from_gzip(self):
        with gzip.open(self.source_definition.get('dump_path'), 'rb') as f:
            self.assertIsInstance(f, gzip.GzipFile)
            line = f.readline()
            doc = json.loads(line.strip())
            self.assertIsInstance(doc, dict)

    def test_content_type(self):
        content_type, doc = self.extractor.run().next()
        self.assertEqual(content_type, 'application/json')
        # Doc is a serialized JSON document, so a string
        self.assertEqual(type(doc), str)


class StaticJSONExtractorTestCase(ExtractorTestCase):
    def setUp(self):
        super(StaticJSONExtractorTestCase, self).setUp()
        self.source_definition['file_url'] = 'http://example.org/dump.json'
        self.extractor = StaticJSONExtractor(self.source_definition)

    def test_dump_path_set(self):
        self.assertIn('file_url', self.source_definition)

    def test_no_dump_path_set(self):
        source_def = self.source_definition
        source_def.pop('file_url')
        with self.assertRaises(ConfigurationError) as cm:
            StaticJSONExtractor(self.source_definition)

    def test_content_type(self):
        # no need to test fetching here, just splitting of items
        content_type, doc = self.extractor.extract_items(
            json.dumps([{'field': 1}])
        ).next()
        self.assertEqual(content_type, 'application/json')
        # Doc is a serialized JSON document, so a string
        self.assertEqual(type(doc), str)
