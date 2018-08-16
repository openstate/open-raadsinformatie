# -*- coding: utf-8 -*-
import re
from string import Formatter

from neo4j.v1 import GraphDatabase
from py2neo import cypher_escape
from copy import copy

from ocd_backend.models.definitions import Prov, Pav, Mapping
from ocd_backend.models.exceptions import QueryResultError, QueryEmptyResult, MissingProperty
from ocd_backend.models.misc import Uri
from ocd_backend.settings import NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD


class AQuoteFormatter(Formatter):
    """Angled quotation marks are used for delimiting parameter keys"""
    parse_regex = re.compile(u'(.[^«]*)«?([^!»]*)?!?([^»]*)?»?', re.DOTALL)

    def parse(self, format_string):
        if format_string:
            for result in self.parse_regex.finditer(format_string):
                yield result.group(1), result.group(2) or None, None, result.group(3) or None


class Neo4jDatabase(object):
    """Database implementation for Neo4j graph database.

    Provides methods for model operations to process ETL data for new and
    existing nodes. When the class is initialized, it reuses the driver if it
    has been used before.
    """
    _driver = None

    HOT = 'Hot'
    COLD = 'Cold'
    ARCHIVE = 'Archive'

    default_params = {
        'was_revision_of': cypher_escape(Uri(Prov, 'wasRevisionOf')),
        'was_derived_from': cypher_escape(Uri(Prov, 'wasDerivedFrom')),
        'had_primary_source': cypher_escape(Uri(Prov, 'hadPrimarySource')),
        'provided_by': cypher_escape(Uri(Pav, 'providedBy')),
        'ori_identifier': cypher_escape(Uri(Mapping, 'ori/identifier')),
    }

    def __init__(self, serializer):
        self.serializer = serializer

        if not self._driver:
            # Set driver on the class so all instances use the same driver
            self._driver = GraphDatabase.driver(
                NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD,), encrypted=False,
            )

        self.session = self._driver.session()
        self.tx = None

    def query(self, query, **params):
        """Executes a query and returns the result"""
        cursor = self.session.run(query, **params)
        result = cursor.data()
        return result

    def transaction_query(self, query, **params):
        """Adds a query to be executed as a transaction. All queries called with
        this method will be in the same transaction until `transaction_commit`
        is called.
        """
        if not self.tx:
            self.tx = self.session.begin_transaction()

        self.tx.run(query, **params)

    def transaction_commit(self):
        """Commits all queries that are added by `transaction_query`."""
        if self.tx:
            result = self.tx.commit()
            self.tx = None  # Make sure the tx is reset
            return result

    def create_constraints(self):
        """Creates constraints on identifiers in Neo4j"""
        self.session.run(
            'CREATE CONSTRAINT ON (x:Hot)'
            'ASSERT x.`{}` IS UNIQUE'.format(Uri(Mapping, 'ori/identifier'))
        )

        self.session.run(
            'CREATE CONSTRAINT ON (x:Live)'
            'ASSERT x.`{}` IS UNIQUE'.format(Uri(Mapping, 'ori/sourceLocator'))
        )

    def get_identifier(self, model_object, **kwargs):
        """Returns the ori identifier based on the specified keyword-argument.

        The ori identifier on a `Hot` node is queried by looking for the source
        identifier on `Cold` nodes. Should return exactly one int or a
        QueryResultError exception."""
        if len(kwargs) != 1:
            raise TypeError('connect takes exactly 1 keyword-argument')

        filter_key, filter_value = kwargs.items()[0]

        label = self.serializer.label(model_object)
        definition = model_object.definition(filter_key)

        params = {
            'n1_labels': u':'.join([self.HOT, cypher_escape(label)]),
            'n2_labels': u':'.join([self.COLD, cypher_escape(label)]),
            'filter_key': cypher_escape(definition.absolute_uri())
        }
        params.update(self.default_params)

        clauses = [
            u'MATCH (n2 :«n2_labels» {«filter_key»: $filter_value})<--(n1 :«n1_labels»)',
            u'RETURN n1.«ori_identifier» AS ori_identifier',
        ]

        fmt = AQuoteFormatter()

        result = self.query(
            fmt.format(u'\n'.join(clauses), **params),
            filter_value=filter_value
        )

        if not result:
            raise MissingProperty(
                'Does not exist: %s with %s=%s' % (model_object.verbose_name(),
                                                   filter_key, filter_value)
            )

        if len(result) > 1:
            raise QueryResultError('The number of results is greater than one!')

        return result[0]['ori_identifier']

    def replace(self, model_object):
        """Replaces or creates nodes based on the model object.

        Existing nodes are replaced by the deflated model object and new ones
        are created when they do not exist. Three queries are run sequentially
        until one of them yields a result.

        The first will add a new version if an older version exists on a node,
        the second will add a new version when no older version exists, the
        third will create new nodes if the nodes do not yet exist. If the third
        query fails, an QueryResultError is raised.

        The first and second query will match the `Cold` node based on the
        source_id.
        """
        fmt = AQuoteFormatter()

        label = self.serializer.label(model_object)
        n2_props = self.serializer.deflate(model_object, props=True, rels=False)

        params = {
            'n1_labels': u':'.join([self.HOT, cypher_escape(label)]),
            'n2_labels': u':'.join([self.COLD, cypher_escape(label)]),
            'n3_labels': self.ARCHIVE,
            'n4_labels': self.ARCHIVE,
            'n5_labels': u':'.join([self.ARCHIVE, cypher_escape(Uri(Prov, 'SoftwareAgent'))]),
        }
        params.update(self.default_params)

        if hasattr(model_object, '_source'):
            # Keep it readable
            # Expand labels
            # Same name variables
            # Escaping some variables
            # Parameters

            # Add a new version if an older version already exists
            clauses = [
                u'MATCH (n1 :«n1_labels»)--(n2 :«n2_labels» {«had_primary_source»: $had_primary_source})-[r2 :«was_revision_of»]-(n3 :«n3_labels»)',
                u'MERGE (n2)-[:«was_revision_of»]->(n4 :«n4_labels»)-[:«was_revision_of»]->(n3)',
                u'MERGE (n2)-[:«provided_by»]->(n5 :«n5_labels» {name: $name})',
                u'SET n4 = n2',
                u'SET n2 = $n2_props',
                u'DELETE r2',
            ]

            cursor = self.session.run(
                fmt.format(u'\n'.join(clauses), **params),
                n2_props=n2_props,
                had_primary_source=model_object.had_primary_source,
                name=model_object._source,
            )
            summary = cursor.summary()
            if summary.counters.relationships_deleted > 0:
                return

            # Add a new version if no older version exists
            clauses = [
                u'MATCH (n1 :«n1_labels»)--(n2 :«n2_labels» {«had_primary_source»: $had_primary_source})',
                u'MERGE (n2)-[:«was_revision_of»]->(n4 :«n4_labels»)',
                u'MERGE (n2)-[:«provided_by»]->(n5 :«n5_labels» {name: $name})',
                u'SET n4 = n2',
                u'SET n2 = $n2_props',
            ]

            cursor = self.session.run(
                fmt.format(u'\n'.join(clauses), **params),
                n2_props=n2_props,
                had_primary_source=model_object.had_primary_source,
                name=model_object._source,
            )
            summary = cursor.summary()
            if summary.counters.nodes_created > 0:
                return

        clauses = [
            u'MATCH (n1 :«n1_labels» {«had_primary_source»: $had_primary_source})',
            u'RETURN n1',
        ]

        cursor = self.session.run(
            fmt.format(u'\n'.join(clauses), **params),
            had_primary_source=model_object.had_primary_source
        )

        n1_props = copy(n2_props)
        if len(cursor.data()) == 0:
            # n1_props = n2_props + ori_identifier
            n1_props[str(Uri(Mapping, 'ori/identifier'))] = \
                model_object.generate_ori_identifier()

        # Create a new entity when no matching node seems to exist
        clauses = [
            u'MERGE (n1 :«n1_labels» {«had_primary_source»: $had_primary_source})-[:«was_derived_from»]->(n2 :«n2_labels»)',
        ]
        bound_params = {}

        if hasattr(model_object, '_source'):
            clauses.extend([
                u'MERGE (n5 :«n5_labels» {name: $name})',
                u'MERGE (n2)-[:«provided_by»]->(n5)',
            ])
            bound_params['name'] = model_object._source
        clauses.extend([
            u'SET n1 = $n1_props',
            u'SET n2 = $n2_props',
            u'RETURN n1.«ori_identifier» AS ori_identifier',
        ])

        cursor = self.session.run(
            fmt.format(u'\n'.join(clauses), **params),
            n1_props=n1_props,
            n2_props=n2_props,
            had_primary_source=model_object.had_primary_source,
            **bound_params
        )
        result = cursor.data()
        if len(result) > 0:
            model_object.ori_identifier = result[0]['ori_identifier']
            return

        raise QueryEmptyResult('No ori_identifier was returned')

    def attach(self, this_object, that_object, rel_type):
        """Attaches this_object to that_object model.

        The query will match the `Cold` node based on the source_id of the
        models. If available it will set `r1_props` on the relation between the
        nodes.
        """
        from .model import Model, Relationship

        fmt = AQuoteFormatter()

        r1_props = dict()
        if isinstance(that_object, Relationship):
            r1_props = that_object.rel
            that_object = that_object.model

        if isinstance(r1_props, Model):
            r1_props = r1_props.serializer.deflate(props=True, rels=True)

        this_label = self.serializer.label(this_object)
        that_label = self.serializer.label(that_object)

        params = {
            'n2_labels': u':'.join([self.COLD, cypher_escape(this_label)]),
            'n3_labels': u':'.join([self.COLD, cypher_escape(that_label)]),
            'r1_labels': cypher_escape(rel_type),
        }
        params.update(self.default_params)

        clauses = [
            u'MATCH (n2 :«n2_labels» {«had_primary_source»: $had_primary_source1})',
            u'MATCH (n3 :«n3_labels» {«had_primary_source»: $had_primary_source2})',
            u'MERGE (n2)-[r1 :«r1_labels»]->(n3)',
            u'SET r1 = $r1_props',
        ]

        self.query(
            fmt.format(u'\n'.join(clauses), **params),
            had_primary_source1=this_object.had_primary_source,
            had_primary_source2=that_object.had_primary_source,
            r1_props=r1_props
        )

    def copy_relations(self):
        """Copies the relations from Cold->Cold nodes to Hot->Hot nodes.

        All relations between these nodes that do not already exist are copied.
        Only direct relations between `Cold` nodes are matched.
        """
        fmt = AQuoteFormatter()

        params = {
            'labels': self.COLD,
            'n1_labels': self.HOT,
            'n2_labels': self.COLD,
            'n3_labels': self.HOT,
        }
        params.update(self.default_params)

        clauses = [
            u'MATCH (n1 :«n1_labels»)-[:«was_derived_from»]->(n2 :«n2_labels»)-[r]->(:«labels»)<-[:«was_derived_from»]-(n3 :«n3_labels»)',
            u'WHERE NOT (n1)--(n3)',
            u'RETURN id(n1) AS id1, id(n2) as id2, id(n3) AS id3, type(r) AS rel, id(startNode(r)) AS start',
        ]

        for result in self.query(fmt.format(u'\n'.join(clauses), **params)):
            clauses = [
                u'MATCH (n1), (n3)',
                u'WHERE id(n1) = $id1',
                u'AND id(n3) = $id3',
                u'MERGE (n1)-[:«rel»]->(n3)'
            ]

            self.query(
                fmt.format(
                    u'\n'.join(clauses),
                    rel=cypher_escape(result['rel']),
                    **params
                ),
                id1=result['id1'],
                id3=result['id3']
            )
