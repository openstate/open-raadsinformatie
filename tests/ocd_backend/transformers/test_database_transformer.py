import os
import json
from unittest import TestCase

from ocd_backend.models.model import Model
from ocd_backend.transformers.database import database_item


class DatabaseTransformerTestCase(TestCase):
    def setUp(self):
        self.PWD = os.path.dirname(__file__)
        self.transformer_class = database_item
        self.transformer_class.get_supplier = self.mock_get_supplier
        self.untested_models = set()

    @staticmethod
    def mock_get_supplier(ori_id):
        if ori_id == 35138:
            return 'allmanak'
        else:
            return 'notubiz'

    def test_transformed_object_properties_equal(self):
        """
        Tests whether the properties of the transformed resource are equal to the properties in the JSON
        dump. Note that date and datetime properties have been removed from the JSON because they are not
        JSON serializable.
        """
        with open(os.path.join(self.PWD, '../test_dumps/database_extracted_meeting.json'), 'r') as f:
            extracted_resource, extracted_subresources = json.loads(f.read())
        args = ('object', (extracted_resource, extracted_subresources), '612019', 'source_item_dummy')
        kwargs = {'source_definition': {
                    'cleanup': 'ocd_backend.tasks.cleanup_elasticsearch',
                    'key': 'groningen',
                }
            }
        transformed_meeting = self.transformer_class.apply(args, kwargs).get()

        # Test properties of the main resource
        extracted_properties = {_prop['predicate']: _prop['value'] for _prop in extracted_resource['properties']
                                if _prop['predicate'] != 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'}
        self.assertEqual(len(transformed_meeting.values), len(extracted_properties))
        for _property in transformed_meeting.values.items():
            if isinstance(_property[1], Model):
                self.untested_models.add(_property[1])
            else:
                self.assertTrue(transformed_meeting.definition(_property[0]).absolute_uri() in extracted_properties)
                self.assertTrue(extracted_properties[transformed_meeting.definition(_property[0]).absolute_uri()] ==
                                _property[1])

        # Test properties of subresources
        for subresource in self.untested_models:
            extracted_subresource_properties = extracted_subresources[subresource.ori_identifier.rsplit('/')[-1]][0]['properties']
            extracted_properties = {_prop['predicate']: _prop['value'] for _prop in extracted_subresource_properties
                                    if _prop['predicate'] != 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'}
            self.assertEqual(len(subresource.values), len(extracted_properties))
            for _property in subresource.values.items():
                if isinstance(_property[1], Model):
                    self.untested_models.add(_property[1])
                else:
                    self.assertTrue(subresource.definition(_property[0]).absolute_uri() in extracted_properties)
                    self.assertTrue(extracted_properties[subresource.definition(_property[0]).absolute_uri()] ==
                                    _property[1])
