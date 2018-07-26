# -*- coding: utf-8 -*-

from neo4j.v1 import GraphDatabase
from pypher import Pypher, Param, __

from ocd_backend.models.definitions import Prov, Pav, Mapping
from ocd_backend.models.exceptions import QueryResultError, QueryEmptyResult
from ocd_backend.models.misc import Uri
from ocd_backend.settings import NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD


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

    def __init__(self, model_class):
        self.serializer = model_class.serializer

        if not self._driver:
            self._driver = GraphDatabase.driver(
                NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD,)
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

    def get_identifier_by_source_id(self, model_object, source_id):
        """Returns the ori identifier based on the specified source identifier.

        The ori identifier on a `Hot` node is queried by looking for the source
        identifier on `Cold` nodes. Should return exactly one int or a
        QueryResultError exception."""
        label = self.serializer.label(model_object)

        q = Pypher()
        q.Match.node('n2', labels=['Cold', label],
                     **{Uri(Prov, 'hadPrimarySource'): source_id}) \
            .rel() \
            .node('n1', labels=['Hot', label])
        q.Return(__.n1.property(Uri(Mapping, 'ori/identifier'))) \
            .As('ori_identifier')

        result = self.query(str(q), **q.bound_params)

        if not result:
            raise QueryResultError('Does not exist')

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
        was_revision_of = Uri(Prov, 'wasRevisionOf')
        provided_by = Uri(Pav, 'providedBy')
        software_agent = Uri(Prov, 'SoftwareAgent')

        label = self.serializer.label(model_object)
        n2_props = self.serializer.deflate(model_object, props=True, rels=False)

        if hasattr(model_object, 'had_primary_source'):
            n2_match = {
                Uri(Prov, 'hasPrimarySource'): model_object.had_primary_source
            }

            # Add a new version if an older version already exists
            q = Pypher()
            q.Match.node('n1', labels=[self.HOT, label]) \
                .rel('r1') \
                .node('n2', labels=[self.COLD, label], **n2_match) \
                .rel('r2', labels=was_revision_of) \
                .node('n3', labels=self.ARCHIVE)  # Match n2 node based on source_id
            q.Merge.node('n2') \
                .rel_out(labels=was_revision_of) \
                .node('n4', labels=self.ARCHIVE) \
                .rel_out(labels=was_revision_of) \
                .node('n3')
            q.Merge.node('n2') \
                .rel_out(labels=provided_by) \
                .node('n5', labels=[self.ARCHIVE, software_agent],
                      name=model_object._source)
            q.Set(__.n4 == __.n2)
            q.Set(__.n2 == Param(name='n2_props', value=n2_props))
            q.Delete('r2')

            cursor = self.session.run(str(q), q.bound_params)
            summary = cursor.summary()
            if summary.counters.relationships_deleted > 0:
                return

            # Add a new version if no older version exists
            q = Pypher()
            q.Match.node('n1', labels=[self.HOT, label]) \
                .rel('r1') \
                .node('n2', labels=[self.COLD, label],
                      **n2_match)  # Match node based on source_id
            q.Merge.node('n2') \
                .rel_out(labels=was_revision_of) \
                .node('n4', labels=[self.ARCHIVE, label])
            q.Merge.node('n2') \
                .rel_out(labels=provided_by) \
                .node('n5', labels=[self.ARCHIVE, software_agent],
                      name=model_object._source)
            q.Set(__.n4 == __.n2)
            q.Set(__.n2 == Param(name='n2_props', value=n2_props))

            cursor = self.session.run(str(q), q.bound_params)
            summary = cursor.summary()
            if summary.counters.nodes_created > 0:
                return

        # Create a new entity when no matching node seems to exist
        q = Pypher()
        q.Match.node('n1', labels=[self.HOT, label], **n2_props)
        q.Return('n1')

        cursor = self.session.run(str(q), q.bound_params)

        n1_props = n2_props
        if len(cursor.data()) == 0:
            # n1_props = n2_props + ori_identifier
            n1_props.update({
                Uri(Mapping, 'ori/identifier'):
                    model_object.generate_ori_identifier()
            })

        # Create a new entity when no matching node seems to exist
        q = Pypher()
        q.Merge.node('n1', labels=[self.HOT, label], **n1_props) \
            .rel_out(labels=Uri(Prov, 'wasDerivedFrom')) \
            .node('n2', labels=[self.COLD, label], **n2_props)
        if hasattr(model_object, '_source'):
            q.Merge.node('n5', labels=[self.ARCHIVE, software_agent],
                         name=model_object._source)
            q.Merge.node('n2') \
                .rel_out(labels=provided_by) \
                .node('n5')
        q.Return(__.n1.property(Uri(Mapping, 'ori/identifier'))) \
            .As('ori_identifier')

        cursor = self.session.run(str(q), q.bound_params)
        a = cursor.data()
        if len(a) > 0:
            model_object.ori_identifier = a[0]['ori_identifier']
            return

        raise QueryEmptyResult('No ori_identifier was returned')

    def attach(self, this_object, that_object, rel_type):
        """Attaches this_object to that_object model.

        The query will match the `Cold` node based on the source_id of the
        models. If available it will set `r1_props` on the relation between the
        nodes.
        """
        from .model import Model, Relationship

        had_primary_source = Uri(Prov, 'hadPrimarySource')

        r1_props = dict()
        if isinstance(that_object, Relationship):
            r1_props = that_object.rel
            that_object = that_object.model

        if isinstance(r1_props, Model):
            r1_props = r1_props.serializer.deflate(props=True, rels=True)

        this_label = self.serializer.label(this_object)
        that_label = self.serializer.label(that_object)

        that_had_primary_source = {}
        if hasattr(that_object, 'had_primary_source'):
            that_had_primary_source = {had_primary_source: that_object.had_primary_source}

        q = Pypher()
        q.Match.node('n2', labels=[self.COLD, this_label],
                     **{had_primary_source: this_object.had_primary_source})
        q.Match.node('n3', labels=[self.COLD, that_label],
                     **that_had_primary_source)
        q.Merge.node('n2') \
            .rel_out('r1', labels=rel_type) \
            .node('n3')
        q.Set(__.r1 == Param(name='r1_props', value=r1_props))

        self.session.run(str(q), q.bound_params)

    def copy_relations(self):
        """Copies the relations from Cold->Cold nodes to Hot->Hot nodes.

        All relations between these nodes that do not already exist are copied.
        Only direct relations between `Cold` nodes are matched.
        """
        was_derived_from = Uri(Prov, 'wasDerivedFrom')

        q = Pypher()
        q.Match.node('n1', labels=self.HOT) \
            .rel_out(labels=was_derived_from) \
            .node('n2', labels=self.COLD) \
            .rel('r') \
            .node(labels=self.COLD) \
            .rel_in(labels=was_derived_from) \
            .node('n3', labels=self.HOT)
        q.Where.Not.node('n1').rel().node('n3')
        q.Return(__.Id('n1').As('id1'),
                 __.Id('n2').As('id2'),
                 __.Id('n3').As('id3'),
                 __.Type(__.r).As('rel'),
                 __.Id(__.startNode(__.r)).As('start'))

        for result in self.query(str(q), **q.bound_params):
            q = Pypher()
            q.Match(__.node('n1'), __.node('n2'))
            q.Where(__.Id('n1') == result['id1']) \
                .And(__.Id('n2') == result['id3'])

            if result['start'] == result['id2']:
                q.Merge.node('n1') \
                    .rel_out(labels=result['rel']) \
                    .node('n2')
            else:
                q.Merge.node('n1') \
                    .rel_in(labels=result['rel']) \
                    .node('n2')

            self.query(str(q), **q.bound_params)
