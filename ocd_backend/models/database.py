# -*- coding: utf-8 -*-

from ocd_backend.settings import NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD
from .definitions import ALL
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
        self.model_class = model_class
        self.serializer = model_class.serializer
        self._driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD,))
        self.session = self._driver.session()

    def labels(self, model_object):
        return [
            self._model_node_label,
            self.serializer.label(model_object),
        ]

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
    def attach_recursive(model_object, q):
        attach = list()
        for rel_type, other_object in model_object.properties(rels=True, props=False):

            #if rel_type == 'https://www.w3.org/TR/2013/REC-prov-o-20130430/#wasDerivedFrom':
            #    continue

            attach.append(model_object.db.attach(model_object, other_object, rel_type, q))

            # End the recursive loop when self-referencing
            if model_object != other_object:
                attach.extend(model_object.db.attach_recursive(other_object, q))
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

        label_string = ":".join(cypher_escape(label) for label in self.labels(self.model_class))

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
        #ori_identifier = self.serializer.get_uri(model_object.get_definition('ori_identifier'))
        source_locator = self.serializer.get_uri(model_object.get_definition('source_locator'))
        rel_type = self.serializer.get_uri(model_object.get_definition('was_derived_from'))

        n_label_string = self.labels(self.model_class)
        #n_property_map = cypher_repr({ori_identifier: model_object.get_ori_identifier()})

        source_identifier = model_object.was_derived_from[0]
        m_label_string = self.labels(source_identifier)
        m_property_map = {source_locator: source_identifier.source_locator}

        replace_params = model_object.deflate(props=True, rels=True)

        q = Pypher()
        q.Merge.node('m', labels=m_label_string, **m_property_map)
        q.Merge.node('n', labels=n_label_string).rel(labels=rel_type).node('m')
        q.SET(__.n == Param(name='replace_params', value=replace_params))
        q.WITH('n')
        q.OPTIONAL.Match.node('n').rel('r').node()
        q.WHERE.NOT.node('n').rel('r', labels=rel_type).node()
        q.DELETE('r')
        q.WITH('n')
        self.attach_recursive(model_object, q)
        #    query += attach
        q.RETURN.DISTINCT('n')

        print q

        # query = CypherDynamicQuery()
        # query += "MERGE (m :«m_labels» «m_props»)"
        # query += "MERGE (n :«n_labels»)-[:«rel!e»]->(m)"
        # #query += "ON CREATE SET n += $replace_params"
        # #query += "ON MATCH SET n += $replace_params"
        # query += "SET n = $replace_params"
        # query += "WITH n"
        # query += "OPTIONAL MATCH (n)-[r]->()"
        # query += "DELETE r"
        # query += "WITH n"



        # query += "MERGE (ox %s)", cypher_repr(other_property_map)
        # query += "MERGE (n)-[rx :%s]->(ox)" % cypher_escape(rel_type)
        # query += "SET ox:%s", other_label_string
        # query += "SET ox = $that_params"
        # query += "SET rx = $rel_params"

        # query += "RETURN DISTINCT n"
        #
        # query.params(
        #     replace_params=replace_params,
        #     n_labels=n_label_string,
        #     m_labels=m_label_string,
        #     m_props=m_property_map,
        #     rel=rel_type,
        # )
        # except Exception, e:
        #     print e

        try:
            cursor = self.session.run(q, q.bound_params)
            result = cursor.data()
        except ConstraintError, e:
            # todo
            raise

        if len(result) != 1:
            raise QueryResultError('The number of results is more or less than one!')
        return result[0]['n']

    def query(self, query, **params):
        cursor = self.session.run(query, **params)
        result = cursor.data()
        return result

    def attach(self, this_object, that_object, rel_type, q):
        from .model import Model, Relationship

        rel_params = dict()
        if isinstance(that_object, Relationship):
            rel_params = that_object.rel
            that_object = that_object.model

        that_params = that_object.deflate(props=True, rels=True)

        if isinstance(rel_params, Model):
            rel_params = rel_params.deflate(props=True, rels=True)

        self_label_string = ":".join(cypher_escape(label) for label in self.labels(this_object))

        identifier = self.serializer.get_uri(this_object.get_definition('ori_identifier'))
        source_locator = self.serializer.get_uri(this_object.get_definition('source_locator'))
        self_property_map = {identifier: this_object.get_ori_identifier()}

        other_label_string = self.labels(that_object)
        other_property_map = {identifier: that_object.get_ori_identifier()}

        from random import randint
        rand = randint(0, 999)
        o = 'o%s' % rand
        s = 's%s' % rand


        q.Merge.node('n').rel_out(s, rel_type).node(o)
        q.SET(getattr(__, o).label(other_label_string))
        q.SET(getattr(__, o) == Param('that_params%s' % rand, that_params))
        q.SET(getattr(__, s) == Param('rel_params%s' % rand, rel_params))

        print
        # query = CypherQuery(o=CypherVar())
        # query('MERGE ({o} {name: «b»}})', other_property_map)
        # query('MERGE ({x} {name: «b»}})', x=CypherVar())
        # query('MERGE (n)-[r :«rel»]->({o})', rel=None)
        # query('SET {o} = ${that_params}').params(that_params=that_params)
        # query('SET {o} = ${that_params}').params(that_params=that_params)
        # query('SET {o}:{}', other_label_string)

        # query = CypherQuery()
        # query('MERGE (o)')
        # #query('MERGE (x {name: «b»})')
        # query('MERGE (n)-[s :«rel!e»]->(o)')
        # query('SET o:«labels»')
        # query('SET o = $that_params')
        # query('SET s = $rel_params')


        #query._vars.update({'x': CypherVar()})
        # query.params(**{
        #     'o': 'o',
        #     'x': 'x',
        #     'b': other_property_map,
        #     'rel': 'abcd',
        #     #'that_params': that_params,
        #     'labels': other_label_string,
        # })

        # o = CypherVariable('o')
        # s = CypherVariable('s')
        #
        # query.params(
        #     **{
        #         'o': o,
        #         'b': other_property_map,
        #         's': s,
        #         'rel': rel_type,
        #         'that_params': that_params,
        #         'rel_params': rel_params,
        #         'labels': other_label_string,
        #     }
        # )


        #query.format()

        #query.validate()

        # a = query.format(**{
        #     'b': other_property_map,
        #     'rel': 'abcd',
        #     'that_params': that_params,
        #     'labels': other_label_string,
        # })

        # b = str(query)
        # print query.global_vars

        # query += "MERGE (ox %s)", cypher_repr(other_property_map)
        # query += "MERGE (n)-[rx :%s]->(ox)", cypher_escape(rel_type)
        # query.format('{:h} {n} {:n}', n=None, r=None, rel=None, o=None)
        # query += "ON CREATE SET ox += $that_params"
        # query += "ON MATCH SET ox += $that_params"
        # query += "SET ox = $that_params"
        # query.set('ox', params=that_params)
        # query += "SET ox:%s", other_label_string
        # query.set('ox', labels=other_label_string)
        # query += "SET rx = $rel_params"
        # query('RETURN {o}')

        # query += "MATCH (n :%s %s)" % (self_label_string, cypher_repr(self_property_map))
        # query += "MERGE (m %s)", cypher_repr(other_property_map)
        # query += "MERGE (n)-[r :%s]->(m)" % cypher_escape(rel_type)
        # query += "ON CREATE SET m += $that_params"
        # query += "ON MATCH SET m += $that_params"
        # query += "SET m:%s", other_label_string
        # query += "SET r = $rel_params"
        # query += "RETURN n"

        #query.set_params(that_params=that_params, rel_params=rel_params)

        # try:
        #     cursor = self.session.run(query, that_params=that_params, rel_params=rel_params)
        #     result = cursor.data()
        # except ConstraintError, e:
        #     raise

        #return query
