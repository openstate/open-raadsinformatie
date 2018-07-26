from unittest import TestCase
from ocd_backend.models import Organization
from ocd_backend.models.misc import Uri
from ocd_backend.models.definitions import Mapping
from ocd_backend.models.exceptions import MissingProperty


class ModelTestCase(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_empty_model(self):
        model = Organization()
        model.save()
        print
