from unittest import TestCase
from ocd_backend.models.database import Neo4jDatabase
from ocd_backend.models.serializers import Neo4jSerializer
from ocd_backend.models.model import Model
from ocd_backend.models import Organization, AlmanakOrganizationName, CbsIdentifier
from ocd_backend.models.misc import URI
from ocd_backend.models.definitions import MAPPING


class DatabaseTestCase(TestCase):
    def setUp(self):
        self.db = Neo4jDatabase(Model())
        self.db.query('MATCH (n) DETACH DELETE n')

        # Assure we are using the test.db
        result = self.db.query('CALL dbms.listConfig()')
        config = {x['name']: x['value'] for x in result}
        assert config['dbms.active_database'] == 'test.db', \
            'Neo4j selected database should be test.db.' \
            'Make sure to use docker-compose.test.yaml'

        self.db.create_constraints()

    def tearDown(self):
        self.db.query('MATCH (n) DETACH DELETE n')

    # def test_replace(self):
    #     object_model = Organization('CBS', 'GM0361', 'Alkmaar')
    #     object_model.name = 'Alkmaar'
    #     object_model.classification = u'Municipality'
    #     object_model.description = 'De gemeente Alkmaar'
    #
    #     a = Organization('CBS', 'CBSa', 'Alkmaar')
    #     a.name = 'a'
    #
    #     b = Organization('CBS', 'CBSb', 'Alkmaar')
    #     b.name = 'b'
    #
    #     object_model.parent = [a, b]
    #     # object_model.parent = Relationship(a, b, rel=c)
    #
    #     object_model.save()
    #
    #     result = self.db.query('MATCH (n) WITH COUNT(n) AS nodes '
    #                            'MATCH (m)-->() RETURN nodes, COUNT(m) AS rels')
    #     self.assertEqual(result[0]['nodes'], 5)
    #     self.assertEqual(result[0]['rels'], 6)

    def test_replace_nodes(self):
        object_model = Organization(URI(MAPPING, 'cbs/identifier'), 'GM0361', 'Alkmaar')
        object_model.name = 'Alkmaar'
        object_model.classification = u'Municipality'
        object_model.description = 'De gemeente Alkmaar'

        a = Organization(URI(MAPPING, 'cbs/identifier'), 'CBSa', 'Alkmaar')
        a.name = 'a'

        b = Organization(URI(MAPPING, 'cbs/identifier'), 'CBSb', 'Alkmaar')
        b.name = 'b'

        object_model.parent = [a, b]
        object_model.save()

        first_identifier = object_model.get_ori_identifier()

        result = self.db.query('MATCH (n) WITH COUNT(n) AS nodes '
                               'MATCH (m)-->() RETURN nodes, COUNT(m) AS rels')
        self.assertEqual(result[0]['nodes'], 7)
        self.assertEqual(result[0]['rels'], 10)

        # Make a new object that matches everything but description
        object_model = Organization(URI(MAPPING, 'cbs/identifier'), 'GM0361', 'Alkmaar')
        object_model.name = 'Alkmaar'
        object_model.classification = u'Municipality'
        object_model.description = 'De gemeente Alkmaar bestaat al lang'

        a = Organization(URI(MAPPING, 'cbs/identifier'), 'CBSa', 'Alkmaar')
        a.name = 'a'

        b = Organization(URI(MAPPING, 'cbs/identifier'), 'CBSb', 'Alkmaar')
        b.name = 'b'

        object_model.parent = [a, b]
        object_model.save()

        result = self.db.query('MATCH (n) WITH COUNT(n) AS nodes '
                               'MATCH (m)-->() RETURN nodes, COUNT(m) AS rels')
        self.assertEqual(result[0]['nodes'], 10)
        self.assertEqual(result[0]['rels'], 13)

        second_identifier = object_model.get_ori_identifier()

        object_model = Organization(URI(MAPPING, 'cbs/identifier'), 'GM0361', 'Alkmaar')
        object_model.name = 'Alkmaar'
        object_model.classification = u'Municipality'
        object_model.description = 'MAAR NU CAPS'

        a = Organization(URI(MAPPING, 'cbs/identifier'), 'CBSa', 'Alkmaar')
        a.name = 'a'

        b = Organization(URI(MAPPING, 'cbs/identifier'), 'CBSb', 'Alkmaar')
        b.name = 'b'

        object_model.parent = [a, b]
        object_model.save()

        result = self.db.query('MATCH (n) WITH COUNT(n) AS nodes '
                               'MATCH (m)-->() RETURN nodes, COUNT(m) AS rels')
        self.assertEqual(result[0]['nodes'], 13)
        self.assertEqual(result[0]['rels'], 16)

        self.assertEqual(first_identifier, second_identifier)
