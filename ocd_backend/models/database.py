# -*- coding: utf-8 -*-

from ocd_backend.settings import NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD
from .definitions import ALL
from .namespace import URI
from .definitions import PROV, PAV, MAPPING
from ocd_backend.utils.misc import load_object, iterate
from py2neo.cypher import cypher_escape, cypher_repr
from pypher import Pypher, Param, __
from neo4j.v1 import GraphDatabase
from neo4j.exceptions import ConstraintError
from .exceptions import MissingProperty, QueryResultError
from neo4j_cypher import CypherQuery, CypherDynamicQuery, CypherVariable


class Neo4jDatabase(object):
    __uri_format__ = 'name'
    _model_node_label = 'Model'

    # def __new__(cls, model_class):
    #     """Implement Neo4jDatabase as a Singleton"""
    #     if not hasattr(cls, 'instance'):
    #         cls.instance = super(Neo4jDatabase, cls).__new__(cls)
    #     return cls.instance

    def __init__(self, model_class):
        self.model_class = model_class  # deprecated
        self.serializer = model_class.serializer
        self._driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD,))
        self.session = self._driver.session()
        self.tx = None

    def label(self, model_object):
        return self.serializer.label(model_object)

    def create_constraints(self):
        """Create ori_identifier constraint on Model node label in Neo4j"""
        ori_identifier = self.model_class.get_definition('ori_identifier').get_full_uri()
        source_locator = self.model_class.get_definition('source_locator').get_full_uri()
        constraints = [
            CypherQuery("CREATE CONSTRAINT ON (x:%s) ASSERT x.%s IS UNIQUE",
                        self._model_node_label, cypher_escape(ori_identifier)),
            CypherQuery("CREATE CONSTRAINT ON (x:%s) ASSERT x.%s IS UNIQUE",
                        self._model_node_label, cypher_escape(source_locator)),
        ]

        for query in constraints:
            self.session.run(query)

    def get_or_create(self, identifier_object, **kwargs):
        if len(kwargs) < 1:
            raise TypeError('get() takes exactly 1 keyword-argument')

        definitions = dict(self.model_class.definitions(props=True, rels=True))
        params = list()
        props = list()
        for name, value in kwargs.items():
            try:
                identifier = definitions[name].get_prefix_uri()  # todo get_uri()
                props.append((name, value,))
                params.append(
                    '`%(key)s`: \'%(value)s\'' % {
                        'key': identifier,
                        'value': value,
                    }
                )
            except KeyError:
                raise MissingProperty(
                    "Cannot query '%s' since it's not defined in %s" % (name, self.model_class.__name__))

        # todo lazy returning only the id, instead everything must be inflated
        query = 'MATCH (n {%s}) RETURN n.`govid:oriIdentifier` AS n' % ', '.join(params)
        try:
            result = self._graph.data(query)
        except OSError, e:
            raise

        if len(result) > 1:
            raise QueryResultError('The number of results is greater than one!')

        if len(result) < 1:
            instance = self.model_class()
            return instance

        return self.model_class.inflate({'govid:oriIdentifier': result[0]['n']})  # todo

    # def save(self):
    #     # if not hasattr(self, 'source_locator'):
    #     #     raise RequiredProperty("Required property 'source_locator' has not been set")
    #     # self.update()
    #     self.model.replace()
    #     self.attach_recursive(self.model)
    #     return self

    @staticmethod
    def attach_recursive(model_object):
        attach = list()
        for rel_type, other_object in model_object.properties(rels=True, props=False):

            model_object.db.replace(other_object)
            attach.append(model_object.db.attach(model_object, other_object, rel_type))

            # End the recursive loop when self-referencing
            if model_object != other_object:
                attach.extend(model_object.db.attach_recursive(other_object))

        model_object.db.copy_relations()
        return attach

    def process_node_relation(self, n, r, m):
        def parse_model(uri):
            namespace = entity = None
            for ns in ALL:
                if ns.namespace in uri:
                    namespace = ns
                    entity = uri[len(ns.namespace):]
                    break

            assert namespace
            return namespace, entity,

        props = dict(n)

        labels = list(n.labels)
        labels.remove(self._model_node_label)
        assert len(labels) == 1
        label = labels[0]

        #namespace, entity = parse_model(label)

        from .model import Singleton
        a = Singleton()
        model_class = a.full_uris[label]

        #a, b = parse_model(r.type)
        if hasattr(r, 'type') and r.type:
            props[r.type] = self.process_node_relation(m, None, None)

        return model_class.inflate(**props)

    def get(self, **kwargs):
        if len(kwargs) < 1:
            raise TypeError('get() takes at least 1 keyword-argument')

        property_map = dict()
        for name, value in kwargs.items():
            try:
                identifier = self.model_class.get_definition(name).get_full_uri()
                property_map[identifier] = value
            except KeyError:
                raise MissingProperty(
                    "Cannot query '%s' since it's not defined in %s" % (name, self.model_class.__name__))

        label_string = self.label(self.model_class)

        clauses = CypherQuery()
        clauses.append("MATCH (n :%s %s)" % (label_string, cypher_repr(property_map)))
        clauses.append("OPTIONAL MATCH (n)-[r]-(m)")
        clauses.append("RETURN n, r, m")

        result = self.session.run(clauses).data()

        if not result:
            raise QueryResultError('Does not exist')

        if len(result) > 1:
            raise QueryResultError('The number of results is greater than one!')

        self.process_node_relation(**result[0])

        a = {k: v for k, v in result[0]['n'].items()}
        a[type(result[0][u'r']).__name__] = {k: v for k, v in result[0]['r'].items()}

        return self.model_class.inflate(**a)

    def get_id(self, model_object, source_id):
        n2_match = {URI(MAPPING, 'ori/sourceLocator'): source_id}
        ori_identifier = URI(MAPPING, 'ori/identifier')

        label = self.label(model_object)

        q = Pypher()
        q.Match.node('n2', labels=['Cold', label], **n2_match) \
            .rel() \
            .node('n1', labels=['Hot', label])
        q.RETURN(__.n1.property(ori_identifier)).AS('ori_identifier')

        result = self.query(str(q), **q.bound_params)

        if not result:
            raise QueryResultError('Does not exist')

        if len(result) > 1:
            raise QueryResultError('The number of results is greater than one!')

        return result[0]['ori_identifier']

    def update(self, model_object):
        label_string = ":".join(cypher_escape(label) for label in self.labels(model_object))

        # self.get(ori_identifier=135)

        # identifier = self.get_definition('ori_identifier').get_prefix_uri()
        # property_map = {identifier: self.get_ori_identifier()}
        property_map = self.serializer.deflate(props=True, rels=False)

        clauses = list()
        clauses.append("MERGE (n :%s %s)" % (label_string, cypher_repr(property_map)))
        # clauses.append("MERGE (m :%s %s)" % (label_string, ''))
        # clauses.append("MERGE (n)-[:delta]->(m)")

        statement = "\n".join(clauses)

        cursor = self.session.run(statement)
        return cursor.data()

    def replace(self, model_object):
        ori_identifier = URI(MAPPING, 'ori/identifier')
        rel_type = URI(PROV, 'wasDerivedFrom')

        label = self.label(model_object)

        n2_match = {URI(MAPPING, 'ori/sourceLocator'): model_object.source_locator}
        n2_props = model_object.deflate(props=True, rels=False)

        # MATCH(n1:Hot) < -[r1] - (n2:Cold) - [r2]->(n3:Archive)
        # MERGE(n2) - [:newVersion]->(n4:Archive:Organization {id: 'abcd'}) - [:oldVersion]->(n3)
        # SET n4 = n2
        # SET n2 = {new: 'props'}
        # DELETE r2
        # RETURN n1, n2, n3, n4

        # Add a new version if an older version already exists
        q = Pypher()
        q.Match.node('n1', labels=['Hot', label]) \
            .rel('r1') \
            .node('n2', labels=['Cold', label], **n2_match) \
            .rel('r2', labels=URI(PROV, 'wasRevisionOf')) \
            .node('n3', labels=['Archive'])  # Match node based on source_id
        q.Merge.node('n2') \
            .rel_out(labels=URI(PROV, 'wasRevisionOf')) \
            .node('n4', labels=['Archive']) \
            .rel_out(labels=URI(PROV, 'wasRevisionOf')) \
            .node('n3')
        q.Merge.node('n2') \
            .rel_out(labels=URI(PAV, 'providedBy')) \
            .node('n5', labels=['Archive', URI(PROV, 'SoftwareAgent')], name=model_object.was_derived_from)
        q.SET(__.n4 == __.n2)
        q.SET(__.n2 == Param(name='n2_props', value=n2_props))
        q.DELETE('r2')
        q.RETURN('n1', 'n2', 'n3', 'n4')

        try:
            cursor = self.session.run(str(q), q.bound_params)
            result = cursor.data()
        except ConstraintError, e:
            # todo
            raise

        if len(result) == 1:
            return result[0]['n1']

        # MATCH(n1:Hot) < -[r1] - (n2:Cold)
        # MERGE(n2) - [:newVersion]->(x:Archive:Organization)
        # SET x = n2
        # SET n2 = {new: 'props'}
        # RETURN n1, n2, x

        # Add a new version if no older version exists
        q1 = Pypher()
        q1.Match.node('n1', labels=['Hot', label]) \
            .rel('r1') \
            .node('n2', labels=['Cold', label], **n2_match)  # Match node based on source_id
        q1.Merge.node('n2') \
            .rel_out(labels=URI(PROV, 'wasRevisionOf')) \
            .node('n4', labels=['Archive', label])
        q1.Merge.node('n2') \
            .rel_out(labels=URI(PAV, 'providedBy')) \
            .node('n5', labels=['Archive', URI(PROV, 'SoftwareAgent')], name=model_object.was_derived_from)
        q1.SET(__.n4 == __.n2)
        q1.SET(__.n2 == Param(name='n2_props', value=n2_props))
        q1.RETURN('n1', 'n2', 'n4')

        try:
            cursor = self.session.run(str(q1), q1.bound_params)
            result = cursor.data()
        except ConstraintError, e:
            # todo
            raise

        if len(result) == 1:
            return result[0]['n1']

        # MERGE(n2:Cold:Organization)-[:`newVersion`]->(n4:`Archive`:Organization)
        # RETURN n2, n4

        n1_props = {ori_identifier: model_object.generate_ori_identifier()}
        n1_props.update(n2_props)

        # Create a new entity when the other options have failed
        q2 = Pypher()
        q2.Create.node('n1', labels=['Hot', label], **n1_props) \
            .rel_out(labels=URI(PROV, 'wasDerivedFrom')) \
            .node('n2', labels=['Cold', label], **n2_props)
        q2.Merge.node('n5', labels=['Archive', URI(PROV, 'SoftwareAgent')], name=model_object.was_derived_from)
        q2.Merge.node('n2') \
            .rel_out(labels=URI(PAV, 'providedBy')) \
            .node('n5')
        q2.RETURN('n1', 'n2')

        try:
            cursor = self.session.run(str(q2), q2.bound_params)
            result = cursor.data()
        except ConstraintError, e:
            # todo
            raise

    def query(self, query, **params):
        cursor = self.session.run(query, **params)
        result = cursor.data()
        return result

    def transaction_query(self, query, **params):
        if not self.tx:
            self.tx = self.session.begin_transaction()

        self.tx.run(query, **params)

    def transaction_commit(self):
        if self.tx:
            result = self.tx.commit()
            self.tx = None
            return result

    def attach(self, this_object, that_object, rel_type):
        from .model import Model, Relationship

        r1_props = dict()
        if isinstance(that_object, Relationship):
            r_props = that_object.rel
            that_object = that_object.model

        n3_props = that_object.deflate(props=True, rels=True)

        if isinstance(r1_props, Model):
            r1_props = r1_props.deflate(props=True, rels=True)

        this_label = self.label(this_object)
        that_label = self.label(that_object)

        q = Pypher()
        q.Match.node('n2', labels=['Cold', this_label], **{URI(MAPPING, 'ori/sourceLocator'): this_object.source_locator})
        q.Match.node('n3', labels=['Cold', that_label], **{URI(MAPPING, 'ori/sourceLocator'): that_object.source_locator})
        q.Merge.node('n2') \
            .rel_out('r1', labels=rel_type) \
            .node('n3')
        q.SET(__.n3 == Param(name='n3_props', value=n3_props))
        q.SET(__.r1 == Param(name='r1_props', value=r1_props))
        q.RETURN('n2')

        a = self.query(str(q), **q.bound_params)

    def copy_relations(self):
        # MATCH (n1:Hot)-->(n2:Cold)-[r]->(n3:Cold)
        # RETURN id(n1) AS id1, id(n2) AS id2, type(r) AS rel
        q = Pypher()
        q.Match.node('n1', labels='Hot') \
            .rel_out(labels=URI(PROV, 'wasDerivedFrom')) \
            .node('n2', labels='Cold') \
            .rel('r') \
            .node(labels='Cold') \
            .rel_in(labels=URI(PROV, 'wasDerivedFrom')) \
            .node('n3', labels='Hot')
        q.Where.Not.node('n1').rel().node('n3')
        q.RETURN(__.ID('n1').AS('id1'), __.ID('n2').AS('id2'), __.ID('n3').AS('id3'),
                 __.TYPE(__.r).AS('rel'), __.ID(__.startNode(__.r)).AS('start'))

        x = q
        results = self.query(str(q), **q.bound_params)

        for result in results:
            q = Pypher()
            q.Match(__.node('n1'), __.node('n2'))
            q.Where(__.ID('n1') == result['id1']).AND(__.ID('n2') == result['id3'])

            if result['start'] == result['id2']:
                q.Merge.node('n1') \
                    .rel_out(labels=result['rel']) \
                    .node('n2')
            else:
                q.Merge.node('n1') \
                    .rel_in(labels=result['rel']) \
                    .node('n2')

            self.query(str(q), **q.bound_params)
