import copy
from nose.tools import eq_, assert_raises
from ocd_backend.models import Meeting, Organization, AgendaItem, Person
from ocd_backend.models.model import Model
from ocd_backend.models.properties import Property, Namespace
from ocd_backend.models.exceptions import RequiredProperty
from ocd_backend.models.serializers import Neo4jSerializer, JsonLDSerializer
from ocd_backend.models.database import Neo4jDatabase
from unittest import TestCase


def get_event():
    source_defaults = {
        'source': 'notubiz',
        'source_id_key': 'identifier',
        'organization': 'alkmaar',
    }

    item = Meeting('104ce628-b453-4fc1-9ab5-61383b6c9ab4', **source_defaults)
    item.name = 'Test iBabs event'
    item.chair = 'Chairman'
    item.location = 'Somewhere'

    organization = Organization('MeetingtypeId', **source_defaults)
    item.organization = organization

    item.agenda = [
        AgendaItem('204ce628-b453-4fc1-9ab5-61383b6c9ab4', **source_defaults),
        AgendaItem('304ce628-b453-4fc1-9ab5-61383b6c9ab4', **source_defaults),
    ]

    item.invitee = [
        Person('404ce628-b453-4fc1-9ab5-61383b6c9ab4', **source_defaults),
        Person('504ce628-b453-4fc1-9ab5-61383b6c9ab4', **source_defaults),
    ]

    return item


class ModelTestCase(TestCase):
    def setUp(self):
        self.db = Neo4jDatabase(Neo4jSerializer())
        self.cleanup_neo4j()

    def tearDown(self):
        self.cleanup_neo4j()

    def cleanup_neo4j(self):
        self.db.query('MATCH (n) DETACH DELETE n')

    def results_neo4j(self):
        result = self.db.query('MATCH (n) WITH COUNT(n) AS nodes '
                               'OPTIONAL MATCH (m)-->() RETURN nodes, COUNT(m) AS rels')
        return result[0]['nodes'], result[0]['rels'],

    def test_properties(self):
        mapping = {
            'http://schema.org/name': 'Test iBabs event',
            'http://www.w3.org/ns/prov#hadPrimarySource': 'https://argu.co/voc/mapping/alkmaar/notubiz/identifier/104ce628-b453-4fc1-9ab5-61383b6c9ab4',
            'https://argu.co/voc/mapping/ori/identifier': None,
            'https://argu.co/ns/meeting/chair': 'Chairman',
            'http://schema.org/invitee': Person,
            'http://schema.org/location': 'Somewhere',
            'https://argu.co/ns/meeting/agenda': AgendaItem,
            'http://schema.org/organizer': Organization,
        }
        expected = copy.copy(mapping)

        item = get_event()
        item.save()

        for key, value in item.properties():
            mapping.pop(key, None)
            if isinstance(value, Model):
                # If value is a instance, return its class for easy compare
                value = type(value)

            # Values should be the same as in the mapping
            if expected[key]:
                eq_(expected[key], value)

        # All pairs should be popped from the mapping
        eq_(0, len(mapping))

    def test_required_props(self):
        source_defaults = {
            'source': 'notubiz',
            'source_id_key': 'identifier',
            'organization': 'alkmaar',
        }

        class TestNamespace(Namespace):
            uri = 'http://example.com'
            prefix = 'ex'

        class RequiredModel(TestNamespace, Model):
            oriIdentifier = Property(TestNamespace, 'oriIdentifier')
            ibabsIdentifier = Property(TestNamespace, 'ibabsIdentifier')
            required_prop = Property(TestNamespace, 'required_prop', required=True)

        item = RequiredModel('104ce628-b453-4fc1-9ab5-61383b6c9ab4', **source_defaults)

        with assert_raises(RequiredProperty):
            item.save()

    # def test_model_meta(self):
    #     item = get_event()
    #       .save()
    #
    #     # Is the identifier_key set in Meta
    #     eq_(item.Meta.identifier_key, 'ibabsIdentifier')

    def test_replace(self):
        item = get_event()
        item.db.replace(item)

        # Todo test if the number of first-level attributes is 5
        nodes, rels = self.results_neo4j()
        self.assertEqual(1, nodes)
        self.assertEqual(0, rels)
