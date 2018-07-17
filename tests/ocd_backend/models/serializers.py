from unittest import TestCase
from ocd_backend.models.serializers import RDFSerializer
from ocd_backend.models import Organization
from ocd_backend.models.misc import URI
from ocd_backend.models.definitions import MAPPING
from ocd_backend.models.exceptions import MissingProperty


class SerializersTestCase(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_unsaved_model(self):
        model = Organization(URI(MAPPING, 'cbs/identifier'), 'SomeID0123', 'Alkmaar')

        with self.assertRaises(MissingProperty):
            serializer = RDFSerializer()
            serializer.serialize(model)

    def test_rdf_serializer(self):
        model = Organization(URI(MAPPING, 'cbs/identifier'), 'GM0361', 'Alkmaar')
        model.save()

        serializer = RDFSerializer()
        a = serializer.serialize(model)
        print a
