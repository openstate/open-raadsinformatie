from unittest import TestCase
from ocd_backend.models.serializers import RdfSerializer
from ocd_backend.models import Organization
from ocd_backend.models.misc import Uri
from ocd_backend.models.definitions import Mapping
from ocd_backend.models.exceptions import MissingProperty


class SerializersTestCase(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_unsaved_model(self):
        source_defaults = {
            'source': 'cbs',
            'source_id_key': 'identifier',
            'organization': 'alkmaar',
        }

        model = Organization('SomeID0123', **source_defaults)

        with self.assertRaises(MissingProperty):
            serializer = RdfSerializer()
            serializer.serialize(model)

    def test_rdf_serializer(self):
        source_defaults = {
            'source': 'cbs',
            'source_id_key': 'identifier',
            'organization': 'alkmaar',
        }

        model = Organization('GM0361', **source_defaults)
        model.save()

        serializer = RdfSerializer()
        serializer.serialize(model)
