import ocd_backend
from py2neo import Graph
import copy
from nose.tools import eq_, assert_raises
from ocd_backend.models import Meeting, Organization, AgendaItem, Person
from ocd_backend.models.model import Model
from ocd_backend.models.properties import Property, Namespace
from ocd_backend.models.exceptions import RequiredProperty
#ocd_backend.settings.NEO4J_GRAPH = Graph("http://neo4j:tests@localhost:7474/db/data/")
from unittest import TestCase


def get_event():
    item = Meeting('ibabsIdentifier', '104ce628-b453-4fc1-9ab5-61383b6c9ab4')
    item.name = 'Test iBabs event'
    item.chair = 'Chairman'
    item.location = 'Somewhere'

    organization = Organization('attribute', 'MeetingtypeId', temporary=True)
    organization.value = 1
    item.organization = organization

    item.agenda = [
        AgendaItem('ibabsIdentifier', '204ce628-b453-4fc1-9ab5-61383b6c9ab4',
                   rel_params={'rdf': '_1'}),
        AgendaItem('ibabsIdentifier', '304ce628-b453-4fc1-9ab5-61383b6c9ab4',
                   rel_params={'rdf': '_2'}),
    ]

    item.invitee = [
        Person('ibabsIdentifier', '404ce628-b453-4fc1-9ab5-61383b6c9ab4'),
        Person('ibabsIdentifier', '504ce628-b453-4fc1-9ab5-61383b6c9ab4'),
    ]

    return item


def cleanup_neo4j():
    from ocd_backend.settings import NEO4J_URL
    Graph(NEO4J_URL).data("MATCH (n) DETACH DELETE n")


class ModelsTestCase(TestCase):
    def setUp(self):
        #cleanup_neo4j()
        pass

    # def tearDown(self):
    #     cleanup_neo4j()

    def test_deflate(self):
        item = get_event()
        deflated = item.deflate()
        expected = {'council:chair': 'Chairman', 'govid:ibabsIdentifier': '104ce628-b453-4fc1-9ab5-61383b6c9ab4', 'schema:name': 'Test iBabs event', 'schema:location': 'Somewhere', 'govid:oriIdentifier': '299a160583d7760058593c032ba12fe8f62df7a2'}

        # Deflate output should match expected dict
        eq_(deflated, expected)

    def test_properties(self):
        mapping = {
            'schema:name': 'Test iBabs event',
            'govid:ibabsIdentifier': '104ce628-b453-4fc1-9ab5-61383b6c9ab4',
            'govid:oriIdentifier': '299a160583d7760058593c032ba12fe8f62df7a2',
            'council:chair': 'Chairman',
            'schema:invitee': Person,
            'schema:location': 'Somewhere',
            'council:agenda': AgendaItem,
            'schema:organizer': Organization,
        }
        expected = copy.copy(mapping)

        item = get_event()
        for key, value in item.properties():
            mapping.pop(key, None)
            if isinstance(value, Model):
                # If value is a instance, return its class for easy compare
                value = type(value)

            # Values should be the same as in the mapping
            eq_(value, expected[key])

        # All pairs should be popped from the mapping
        eq_(len(mapping), 0)

    def test_required_props(self):
        ns = Namespace('http://example.com', 'ex')

        class RequiredModel(Model):
            oriIdentifier = Property(ns, 'oriIdentifier')
            ibabsIdentifier = Property(ns, 'ibabsIdentifier')
            required_prop = Property(ns, 'required_prop', required=True)

            class Meta:
                namespace = ns

        item = RequiredModel('ibabsIdentifier', '104ce628-b453-4fc1-9ab5-61383b6c9ab4')

        with assert_raises(RequiredProperty):
            item.save()

    def test_model_meta(self):
        item = get_event()

        # Is the identifier_key set in Meta
        eq_(item.Meta.identifier_key, 'ibabsIdentifier')

    def test_replace(self):
        item = get_event()
        result = item.replace()

        # Test if the number of first-level attributes is 5
        eq_(len(result), 5)

    def test_attach(self):
        item = get_event()
        result = item.replace()

        # Test if the number of first-level attributes is 5
        eq_(len(result), 5)


# Import test modules here so the noserunner can pick them up, and the
# ModelsTestCase is parsed. Add additional testcases when required
from .neo4j import Neo4jTestCase
from .database import DatabaseTestCase
