import json
import os

from ocd_backend.items import LocalDumpItem

from . import ItemTestCase


class LocalDumpItemTestCase(ItemTestCase):
    def setUp(self):
        super(LocalDumpItemTestCase, self).setUp()
        self.PWD = os.path.dirname(__file__)
        dump_path = os.path.abspath(os.path.join(self.PWD, '../test_dumps/ocd_openbeelden_test.gz'))
        self.source_definition = {
            'id': 'test_definition',
            'extractor': 'ocd_backend.extractors.staticfile.StaticJSONDumpExtractor',
            'transformer': 'ocd_backend.transformers.BaseTransformer',
            'item': 'ocd_backend.items.LocalDumpItem',
            'loader': 'ocd_backend.loaders.ElasticsearchLoader',
            'dump_path': dump_path,
            'index_name': 'openbeelden'
        }

        with open(os.path.abspath(os.path.join(self.PWD, '../test_dumps/item.json')), 'r') as f:
            self.raw_item = f.read()
        with open(os.path.abspath(os.path.join(self.PWD, '../test_dumps/item.json')), 'r') as f:
            self.item = json.load(f)

        self.collection = u'Open Beelden'
        self.rights = u'Creative Commons Attribution-ShareAlike'
        self.original_object_id = u'oai:openimages.eu:749181'
        self.original_object_urls = {
            u'xml': u'http://openbeelden.nl/feeds/oai/?verb=GetRecord&identifie'
                    u'r=oai:openimages.eu:749181&metadataPrefix=oai_oi',
            u'html': u'http://openbeelden.nl/media/749181/'
        }

    def test_item_collection(self):
        item = LocalDumpItem(self.source_definition, 'application/json',
                             self.raw_item, self.item, None)
        self.assertEqual(item.get_collection(), self.collection)

    def test_get_rights(self):
        item = LocalDumpItem(self.source_definition, 'application/json',
                             self.raw_item, self.item, None)
        self.assertEqual(item.get_rights(), self.rights)

    def test_get_original_object_id(self):
        item = LocalDumpItem(self.source_definition, 'application/json',
                             self.raw_item, self.item, None)
        self.assertEqual(item.get_original_object_id(), self.original_object_id)


    def test_get_original_object_urls(self):
        item = LocalDumpItem(self.source_definition, 'application/json',
                             self.raw_item, self.item, None)
        self.assertDictEqual(item.get_original_object_urls(),
                             self.original_object_urls)


    def test_get_object_model(self):
        item = LocalDumpItem(self.source_definition, 'application/json',
                             self.raw_item, self.item, None)
        self.assertIsInstance(item.get_object_model(), dict)

    def test_get_index_data(self):
        item = LocalDumpItem(self.source_definition, 'application/json',
                             self.raw_item, self.item, None)
        self.assertIsInstance(item.get_index_data(), dict)

    def test_get_all_text(self):
        item = LocalDumpItem(self.source_definition, 'application/json',
                             self.raw_item, self.item, None)
        self.assertEqual(type(item.get_all_text()), unicode)
        self.assertTrue(len(item.get_all_text()) > 0)

    def test_combined_index_data_types(self):
        item = LocalDumpItem(self.source_definition, 'application/json',
                             self.raw_item, self.item, None)
        data = item.get_object_model()
        for field, field_type in item.combined_index_fields.iteritems():
            self.assertIn(field, data)
            self.assertIsInstance(data[field], field_type)
