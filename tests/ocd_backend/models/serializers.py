from unittest import TestCase
from ocd_backend.models.serializers import RdfSerializer
from ocd_backend.models import Organization
from ocd_backend.models.exceptions import MissingProperty


class SerializersTestCase(TestCase):

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

    # def test_deflate(self):
    #     item = get_event()
    #     item.save()
    #
    #     serializer = JsonLDSerializer()
    #     deflated = serializer.deflate(item, props=True, rels=True)
    #
    #     # Delete ori_identifier since this will be different every time
    #     del deflated['ori_identifier']
    #
    #     expected = {'name': u'Test iBabs event', 'had_primary_source': u'https://argu.co/voc/mapping/alkmaar/notubiz/identifier/104ce628-b453-4fc1-9ab5-61383b6c9ab4', 'invitee': ['https://id.openraadsinformatie.nl/364', 'https://id.openraadsinformatie.nl/365'], 'location': u'Somewhere', 'agenda': ['https://id.openraadsinformatie.nl/366', 'https://id.openraadsinformatie.nl/367'], 'organization': 'https://id.openraadsinformatie.nl/368', 'chair': u'Chairman'}
    #
    #     # Deflate output should match expected dict
    #     eq_(deflated, expected)
