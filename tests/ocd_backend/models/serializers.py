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
        model = Organization(Uri(Mapping, 'cbs/identifier'), 'SomeID0123', 'Alkmaar')

        with self.assertRaises(MissingProperty):
            serializer = RdfSerializer()
            serializer.serialize(model)

    def test_rdf_serializer(self):
        model = Organization(Uri(Mapping, 'cbs/identifier'), 'GM0361', 'Alkmaar')
        model.save()

        serializer = RdfSerializer()
        a = serializer.serialize(model)
        print a
