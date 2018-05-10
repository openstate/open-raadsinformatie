from ocd_backend.settings import NEO4J_URL
from py2neo import Graph
import ocd_backend.models
from nose.tools import eq_
from . import ModelsTestCase, get_event


graph = Graph(NEO4J_URL)


class Neo4jTestCase(ModelsTestCase):
    def test_attributes_exist(self):
        # Events should have a name
        result = graph.data("MATCH (n :`opengov:Event`) WHERE NOT exists(n.`schema:name`) RETURN n")

        # Query should come out empty
        eq_(len(result), 0)

        result = graph.data("MATCH (n) WHERE NOT exists(n.`govid:oriIdentifier`) RETURN n")

        # Query should come out empty
        eq_(len(result), 0)

    def test_node_labels(self):
        node_labels = graph.data("MATCH (n) RETURN labels(n) as l")

        model_order = {}
        # Warning: ocd_backend.models only features some convenient models
        # this *might* cause unexpected behaviour passing the test.
        for k, v in ocd_backend.models.__dict__.items():
            try:
                issubclass(v, ocd_backend.models.ModelBase)
                if v is ocd_backend.models.ModelBase:
                    continue
                model_order[v.get_prefix_uri()] = v
            except TypeError:
                pass

        for node_label in node_labels:
            cardinality = None
            model = None
            for label in node_label['l']:
                try:
                    mro = len(model_order[label].mro())
                except KeyError:
                    continue

                # Detect edge cases when classes are equally leveled
                assert cardinality != mro

                if not cardinality or cardinality < mro:
                    cardinality = mro
                    model = model_order[label]

                # The model mro should match the labels in the database
                eq_(cmp(sorted(model.labels()), sorted(node_label['l'])), 0)

            # Verify that at least one model was matched
            assert model is not None

    def test_duplicate_events(self):
        item = get_event()
        item.save()
        result = graph.data("MATCH (n {`govid:ibabsIdentifier`: '104ce628-b453-4fc1-9ab5-61383b6c9ab4'}) RETURN n")

        # Query should return just one result
        eq_(len(result), 1)

        # Test if the number of first-level attributes is 5
        eq_(len(result[0]['n']), 5)