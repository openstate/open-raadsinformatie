import os
from unittest import TestCase

import simplejson as json

from ocd_backend.models.model import Model
from ocd_backend.transformers.database import database_item


class DatabaseTransformerTestCase(TestCase):
    def setUp(self):
        self.PWD = os.path.dirname(__file__)
        self.transformer_class = database_item
        self.transformer_class.get_supplier = self.mock_get_supplier
        self.tested_models = set()

    @staticmethod
    def mock_get_supplier(ori_id):
        if ori_id == 35138:
            return 'allmanak'
        else:
            return 'notubiz'

    def test_transformed_object_properties_equal(self):
        with open(os.path.join(self.PWD, '../test_dumps/database_extracted_meeting.json'), 'r') as f:
            extracted_resource, extracted_subresources = json.loads(f.read())
        args = ('object', (extracted_resource, extracted_subresources), '612019', 'source_item_dummy')
        kwargs = {'source_definition': {
                    'cleanup': 'ocd_backend.tasks.cleanup_elasticsearch',
                    'key': 'groningen',
                }
            }
        transformed_meeting = self.transformer_class.apply(args, kwargs).get()

        for _property in transformed_meeting.values.iteritems():
            try:
                self.assertTrue(self.test_properties_equal(_property,
                                                           transformed_meeting,
                                                           extracted_resource,
                                                           extracted_subresources))
            except TypeError, e:
                print e

    def test_properties_equal(self, _property, resource, extracted_resource, extracted_subresources):
        try:
            if isinstance(_property[1], Model):
                if resource.ori_identifier not in self.tested_models:
                    self.tested_models.add(resource.ori_identifier)
                    for _subresource_property in resource.values.iteritems():
                        self.test_properties_equal(_subresource_property,
                                                   resource,
                                                   extracted_resource,
                                                   extracted_subresources)
            else:
                if resource.definition(_property[0]).absolute_uri() in \
                        [_prop['predicate'] for _prop in extracted_resource['properties']]:
                    return True
                else:
                    return False
        except TypeError, e:
            print e

# assert _property[1] == extracted_resource[transformed_meeting.definition(_property[0]).absolute_uri()]