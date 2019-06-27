import datetime
from unittest import TestCase

from ocd_backend.models.postgres_database import PostgresDatabase


class PostgresDatabaseTestCase(TestCase):

    def test_map_column_type(self):
        function = PostgresDatabase.map_column_type

        values = (True, False)
        for value in values:
            self.assertEqual(function(value), 'prop_boolean')

        values = (1, -4, 4024832)
        for value in values:
            self.assertEqual(function(value), 'prop_integer')

        values = (1.5, -4.56, 402.4832)
        for value in values:
            self.assertEqual(function(value), 'prop_float')

        values = (datetime.datetime.now().date(), datetime.datetime.now().date())
        for value in values:
            self.assertEqual(function(value), 'prop_datetime')

        value = "Testing with a text string"
        self.assertEqual(function(value), 'prop_string')
