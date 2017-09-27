import unittest
from ocd_backend.models.model_base import ModelBase
from ocd_backend.models.namespaces import owl, foaf, OPENGOV, SCHEMA, COUNCIL
from ocd_backend.models.property_base import Type, Some, Only, Min, Exactly, SomeString, SomeDate
from ocd_backend.models.exceptions import ValidationError


class Motion(ModelBase):
    _type = Type(OPENGOV)
    name = SomeString(SCHEMA, 'name')


class MyTest(unittest.TestCase):
    def setUp(self):
        self.model = Motion()


    def test_predefined_attributes(self):
        try:
            self.model.abc = 'abc'

            # No exception given so failed
            self.fail("No exception was given!")
        except AttributeError, e:
            pass

    def test_min_restriction(self):

        class MinModel(ModelBase):
            _type = Type(OPENGOV)
            min_test = Min(OPENGOV, 'min_test', 2, str)

        model = MinModel()

        try:
            model.validate()
            # No exception given so failed
            self.fail("No exception was given!")
        except ValidationError, e:
            pass

        model.min_test = 'test'
        self.assertTrue(model.validate())

    def test_exactly_restriction(self):

        class ExactlyModel(ModelBase):
            _type = Type(OPENGOV)
            exactly_test = Exactly(OPENGOV, 'exactly_test', 2, str)

        model = ExactlyModel()

        try:
            model.validate()
            # No exception given so failed
            self.fail("No exception was given!")
        except ValidationError, e:
            pass

        model.exactly_test = ['abc', 'def']
        self.assertTrue(model.validate())