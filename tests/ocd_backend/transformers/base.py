import os.path

from . import TransformerTestCase

from ocd_backend.exceptions import NoDeserializerAvailable
from ocd_backend.transformers import BaseTransformer


class BaseTransformerTestCase(TransformerTestCase):
    def setUp(self):
        super(BaseTransformerTestCase, self).setUp()
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
            self.item = ('application/json', f.read())
        self.transformer = BaseTransformer()
        self.deserialized_item = self.transformer.deserialize_item(*self.item)

    def test_deserializer(self):
        deserialized_item = self.transformer.deserialize_item(*self.item)
        self.assertEqual(deserialized_item, self.deserialized_item)

    def test_no_deserializer_available(self):
        with self.assertRaises(NoDeserializerAvailable):
            item = self.transformer.deserialize_item('application/test',
                                                     self.item[1])

    def test_run(self):
        # This implicitly tests item functionality too. Perhaps we want to mock
        # this?
        combined_object_id, object_id, combi_doc, doc = self.transformer.run(
            *self.item, source_definition=self.source_definition)
        self.assertIsNotNone(object_id)
        self.assertIsNotNone(combi_doc)
        self.assertIsNotNone(doc)
