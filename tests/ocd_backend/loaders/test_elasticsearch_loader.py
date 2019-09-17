import simplejson as json
import os.path

from ocd_backend.exceptions import ConfigurationError
from ocd_backend.loaders.elasticsearch import elasticsearch_loader
from . import LoaderTestCase


class ESLoaderTestCase(LoaderTestCase):
    def setUp(self):
        super(ESLoaderTestCase, self).setUp()
        self.PWD = os.path.dirname(__file__)
        self.object_id = u'52c54e5be11b218b1a6df731634fda9fb2188d57'

        with open(os.path.join(self.PWD, '../test_dumps/combined_index_doc.json'), 'r') as f:
            self.combined_index_doc = json.load(f)

        with open(os.path.join(self.PWD, '../test_dumps/index_doc.json'), 'r') as f:
            self.index_doc = json.load(f)

        dump_path = os.path.abspath(os.path.join(self.PWD, '../test_dumps/ocd_openbeelden_test.gz'))

        self.source_definition = {
            'id': 'test_definition',
            'extractor': 'ocd_backend.extractors.staticfile.StaticJSONDumpExtractor',
            'transformer': 'ocd_backend.transformers.transformer',
            'item': 'ocd_backend.items.LocalDumpItem',
            'loader': 'ocd_backend.loaders.elasticsearch.elasticsearch_loader',
            'dump_path': dump_path
        }
        self.loader = elasticsearch_loader

    def test_throws_configuration_error_without_index_name(self):
        # self.loader.run(source_definition=self.source_definition)
        self.assertRaises(ConfigurationError, self.loader.run,
                          source_definition=self.source_definition)
