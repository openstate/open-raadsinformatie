import os.path
from unittest import TestCase


class ItemTestCase(TestCase):
    def setUp(self):
        self.PWD = os.path.dirname(__file__)
        dump_path = os.path.abspath(
            os.path.join(self.PWD, '..', 'test_dumps/ocd_openbeelden_test.gz')
        )
        self.source_definition = {
            'id': 'test_definition',
            'extractor': (
                'ocd_backend.extractors.staticfile.StaticJSONDumpExtractor'
            ),
            'transformer': 'ocd_backend.transformers.BaseTransformer',
            'item': 'ocd_backend.items.LocalDumpItem',
            'loader': 'ocd_backend.loaders.elasticsearch.ElasticsearchLoader',
            'dump_path': dump_path,
            'index_name': 'openbeelden'
        }


# Import test modules here so the noserunner can pick them up, and the
# ExtractorTestCase is parsed. Add additional testcases when required
#from .localdump import LocalDumpItemTestCase
#from .go_meeting import MeetingItemTestCase
from .notubiz_meeting import NotubizMeetingTestCase
#from .go_report import ReportItemTestCase
