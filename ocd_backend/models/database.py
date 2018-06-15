# -*- coding: utf-8 -*-

from ocd_backend.settings import NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD
from py2neo import Graph #, ConstraintError
from py2neo.cypher import cypher_escape, cypher_repr
from neo4j.v1 import GraphDatabase
from .exceptions import MissingProperty, QueryResultError


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

    def create_constraints(self):
        """Create ori_identifier constraint on Model node label in Neo4j"""
        identifier = self.model_class.get_definition('ori_identifier').get_full_uri()
        self.session.run("CREATE CONSTRAINT ON (x:%s) ASSERT x.%s IS UNIQUE " %
                        (self._model_node_label, cypher_escape(identifier)))

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
                raise MissingProperty("Cannot query '%s' since it's not defined in %s" % (name, self.model_class.__name__))

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

        return self.model_class.inflate({'govid:oriIdentifier': result[0]['n']}) #todo

    # def save(self):
    #     # if not hasattr(self, 'source_locator'):
    #     #     raise RequiredProperty("Required property 'source_locator' has not been set")
    #     # self.update()
    #     self.model.replace()
    #     self.attach_recursive(self.model)
    #     return self

    @staticmethod
    def attach_recursive(model_object):
        for rel_type, other_object in model_object.properties(rels=True, props=False):
            model_object.db.attach(model_object, other_object, rel_type)

            # End the recursive loop when self-referencing
            if model_object != other_object:
                model_object.db.attach_recursive(other_object)

    # def process_node_relation(self, n, r, m):
    #     n_properties = n.items()
    #     for

    def get(self, **kwargs):
        if len(kwargs) < 1:
            raise TypeError('get() takes at least 1 keyword-argument')

        property_map = dict()
        for name, value in kwargs.items():
            try:
                identifier = self.model_class.get_definition(name).get_full_uri()
                property_map[identifier] = value
            except KeyError:
                raise MissingProperty("Cannot query '%s' since it's not defined in %s" % (name, self.model_class.__name__))

        label_string = ":".join(cypher_escape(label) for label in self.serializer.labels(self.model_class))

        clauses = list()
        clauses.append("MATCH (n :%s %s)" % (label_string, cypher_repr(property_map)))
        clauses.append("OPTIONAL MATCH (n)-[r]-(m)")
        clauses.append("RETURN n, r, m")

        statement = "\n".join(clauses)

        result = self.session.run(statement).data()

        if not result:
            raise QueryResultError('Does not exist')

        if len(result) > 1:
            raise QueryResultError('The number of results is greater than one!')

        self.process_node_relation(**result[0])

        a = {k: v for k, v in result[0]['n'].items()}
        a[type(result[0][u'r']).__name__] = {k: v for k, v in result[0]['r'].items()}

        inflated = self.model_class.inflate(**a)
        print

    def update(self, model_object):
        label_string = ":".join(cypher_escape(label) for label in self.serializer.labels(model_object))

        # self.get(ori_identifier=135)

        # identifier = self.get_definition('ori_identifier').get_prefix_uri()
        # property_map = {identifier: self.get_ori_identifier()}
        property_map = self.serializer.deflate(namespaces='full', props=True, rels=False)

        clauses = list()
        clauses.append("MERGE (n :%s %s)" % (label_string, cypher_repr(property_map)))
        # clauses.append("MERGE (m :%s %s)" % (label_string, ''))
        # clauses.append("MERGE (n)-[:delta]->(m)")

        statement = "\n".join(clauses)

        tx = self._graph.begin()
        res = tx.run(statement)
        tx.commit()

        print

    def replace(self, model_object):
        query = '''
        MERGE (n :`%(labels)s` {`govid:oriIdentifier`: '%(identifier_value)s'})
        SET n = $replace_params
        WITH n
        OPTIONAL MATCH (n)-[r]->()
        DELETE r
        WITH n
        RETURN DISTINCT n
        '''

        try:
            cursor = self.session.run(
                query % {'labels': '`:`'.join(self.serializer.labels(model_object)), 'identifier_value': model_object.get_ori_identifier()},
                replace_params=model_object.deflate(props=True, rels=False))
            result = cursor.data()
        except OSError, e:
            # todo
            raise

        if len(result) != 1:
            raise QueryResultError('The number of results is more or less than one!')
        return result[0]['n']

    def attach(self, this_object, that_object, rel_type):
        from .model import Model, Relationship

        rel_params = dict()
        if isinstance(that_object, Relationship):
            rel_params = that_object.rel
            that_object = that_object.model

        that_params = that_object.deflate(props=True, rels=True)

        if isinstance(rel_params, Model):
            rel_params = rel_params.deflate(props=True, rels=True)

        self_label_string = ":".join(cypher_escape(label) for label in self.serializer.labels(this_object))

        identifier = self.serializer.get_uri(this_object.get_definition('ori_identifier'))
        self_property_map = {identifier: this_object.get_ori_identifier()}

        other_label_string = ":".join(cypher_escape(label) for label in self.serializer.labels(that_object))
        other_property_map = {identifier: this_object.get_ori_identifier()}

        clauses = list()
        clauses.append("MATCH (n :%s %s)" % (self_label_string, cypher_repr(self_property_map)))
        clauses.append("MERGE (m %s)" % cypher_repr(other_property_map))
        clauses.append("MERGE (n)-[r :%s]->(m)" % cypher_escape(rel_type))
        clauses.append("ON CREATE SET m += $that_params")
        clauses.append("ON MATCH SET m += $that_params")
        clauses.append("SET m:%s" % other_label_string)
        clauses.append("SET r = $rel_params")
        clauses.append("RETURN n")

        statement = "\n".join(clauses)

        tx = self._graph.begin()
        try:
            cursor = tx.run(statement, that_params=that_params, rel_params=rel_params)
            tx.commit()
        except ConstraintError, e:
            raise

        result = cursor.data()

        return result
