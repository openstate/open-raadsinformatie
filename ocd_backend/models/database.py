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


fmt = AQuoteFormatter()


class Neo4jDatabase(object):
    """Database implementation for Neo4j graph database.

    Provides methods for model operations to process ETL data for new and
    existing nodes. When the class is initialized, it reuses the driver if it
    has been used before.
    """
    default_params = {
        'was_revision_of': cypher_escape(Uri(Prov, 'wasRevisionOf')),
        'was_derived_from': cypher_escape(Uri(Prov, 'wasDerivedFrom')),
        'had_primary_source': cypher_escape(Uri(Prov, 'hadPrimarySource')),
        'provided_by': cypher_escape(Uri(Pav, 'providedBy')),
        'ori_identifier': cypher_escape(Uri(Mapping, 'ori/identifier')),
    }

    # Set driver on the class so all instances use the same driver
    driver = GraphDatabase.driver(
        NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD,), encrypted=False,
    )

    def __init__(self, serializer):
        self.serializer = serializer
        self.tx = None

    def query(self, query, **params):
        """Executes a query and returns the result"""
        with self.driver.session() as session:
            cursor = session.run(query, **params)
            result = cursor.data()
        return result

    @property
    def session(self):
        return self.driver.session()

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
            'labels': cypher_escape(label),
            'filter_key': cypher_escape(definition.absolute_uri())
        }
        params.update(self.default_params)

        clauses = [
            u'MATCH (n :«labels» {«filter_key»: $filter_value})',
            u'RETURN n.«ori_identifier» AS ori_identifier',
        ]

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
        labels = self.serializer.label(model_object)

        params = {
            'labels': cypher_escape(labels),
            'had_primary_source': cypher_escape(Uri(Prov, 'hadPrimarySource')),
        }
        params.update(self.default_params)

        if not model_object.values.get('had_primary_source'):

            from ocd_backend.models.model import Individual
            if isinstance(model_object, Individual):
                if not model_object.values.get('ori_identifier'):
                    model_object.generate_ori_identifier()

                props = self.serializer.deflate(model_object, props=True, rels=False)

                clauses = [
                    u'MERGE (n :«labels»)',
                    u'SET n += $props',
                    u'RETURN n',
                ]

                cursor = self.session.run(
                    fmt.format(u'\n'.join(clauses), **params),
                    props=props,
                )
                summary = cursor.summary()
            else:
                self._create_blank_node(model_object)
        else:
            # if ori_identifier is already known use that to identify instead
            if model_object.values.get('ori_identifier'):
                self._merge(model_object)
            else:
                clauses = [
                    u'MATCH (n :«labels»)',
                    u'WHERE $had_primary_source IN n.«had_primary_source»',
                    u'RETURN n.«ori_identifier» AS ori_identifier',
                ]

                cursor = self.session.run(
                    fmt.format(u'\n'.join(clauses), **params),
                    had_primary_source=model_object.had_primary_source,
                )
                result = cursor.data()

                if len(result) > 1:
                    # Todo don't fail yet until unique constraints are solved
                    # raise QueryResultError('The number of results is greater than one!')
                    pass

                try:
                    ori_identifier = result[0]['ori_identifier']
                except Exception:
                    ori_identifier = None

                if ori_identifier:
                    model_object.ori_identifier = ori_identifier
                    self._merge(model_object)
                else:
                    # if ori_identifier do merge otherwise create
                    self._create_node(model_object)

            # raise QueryEmptyResult('No ori_identifier was returned')

    def _create_node(self, model_object):
        if not model_object.values.get('ori_identifier'):
            model_object.generate_ori_identifier()

        labels = self.serializer.label(model_object)
        props = self.serializer.deflate(model_object, props=True, rels=False)

        params = {
            'labels': cypher_escape(labels),
        }
        params.update(self.default_params)

        clauses = [
            u'CREATE (n :«labels» {«had_primary_source»: [$had_primary_source]})',
            u'SET n += $props',
            u'RETURN n',
        ]

        cursor = self.session.run(
            fmt.format(u'\n'.join(clauses), **params),
            props=props,
            had_primary_source=model_object.had_primary_source,
        )
        summary = cursor.summary()

    def _create_blank_node(self, model_object):
        if not model_object.values.get('ori_identifier'):
            model_object.generate_ori_identifier()

        labels = self.serializer.label(model_object)
        props = self.serializer.deflate(model_object, props=True, rels=False)

        params = {
            'labels': cypher_escape(labels),
        }
        params.update(self.default_params)

        clauses = [
            u'CREATE (n :«labels»)',
            u'SET n += $props',
            u'RETURN n',
        ]

        cursor = self.session.run(
            fmt.format(u'\n'.join(clauses), **params),
            props=props,
        )
        summary = cursor.summary()

    def _merge(self, model_object):
        labels = self.serializer.label(model_object)
        props = self.serializer.deflate(model_object, props=True, rels=False)

        # todo this quickfix needs to be refactored
        del props[Uri(Prov, 'hadPrimarySource')]

        params = {
            'labels': cypher_escape(labels),
        }
        params.update(self.default_params)

        clauses = [
            u'MERGE (n :«labels» {«ori_identifier»: $ori_identifier})',
            u'SET n += $props',
            u'SET(',  # Only add had_primary_source to array if doesn't exist
            u'  CASE WHEN NOT $had_primary_source IN n.«had_primary_source» THEN n END',
            u').«had_primary_source» = n.«had_primary_source» + [$had_primary_source]',
            u'WITH n',
            u'OPTIONAL MATCH (n)-->(m)',  # Remove all directly related blank nodes
            u'WHERE NOT EXISTS(m.«had_primary_source»)',
            u'DETACH DELETE m',
            u'WITH n',
            u'OPTIONAL MATCH (n)-[r]->()',  # Remove all outgoing relationships
            u'DELETE r',
            u'WITH n',
            u'RETURN n',
        ]

        cursor = self.session.run(
            fmt.format(u'\n'.join(clauses), **params),
            had_primary_source=model_object.had_primary_source,
            ori_identifier=model_object.ori_identifier,
            props=props,
        )
        summary = cursor.summary()

    def attach(self, this_object, that_object, rel_type):
        """Attaches this_object to that_object model.

        The query will match the `Cold` node based on the source_id of the
        models. If available it will set `r1_props` on the relation between the
        nodes.
        """
        from .model import Model, Relationship

        r1_props = dict()
        if isinstance(that_object, Relationship):
            r1_props = that_object.rel
            that_object = that_object.model

        if isinstance(r1_props, Model):
            r1_props = r1_props.serializer.deflate(props=True, rels=True)

        this_label = self.serializer.label(this_object)
        that_label = self.serializer.label(that_object)

        params = {
            'n2_labels': cypher_escape(this_label),
            'n3_labels': cypher_escape(that_label),
            'r1_labels': cypher_escape(rel_type),
        }
        params.update(self.default_params)

        clauses = [
            u'MATCH (n2 :«n2_labels» {«ori_identifier»: $ori_identifier1})',
            u'MATCH (n3 :«n3_labels» {«ori_identifier»: $ori_identifier2})',
            u'MERGE (n2)-[r1 :«r1_labels»]->(n3)',
            u'SET r1 = $r1_props',
        ]

        self.query(
            fmt.format(u'\n'.join(clauses), **params),
            ori_identifier1=this_object.ori_identifier,
            ori_identifier2=that_object.ori_identifier,
            r1_props=r1_props
        )
