from unittest import TestCase

from ocd_backend.utils.misc import slugify
from ocd_backend.utils.misc import iterate
from ocd_backend.utils.misc import compare_insensitive


class SlugifyTestCase(TestCase):
    def test_ascii_characters(self):
        self.assertEqual(slugify('test'), 'test')
        self.assertEqual(slugify('test123'), 'test123')
        self.assertEqual(slugify('test-test'), 'test-test')
        self.assertEqual(slugify('test$test'), 'test-test')
        self.assertEqual(slugify('test#%.#D$test'), 'test-d-test')

    def test_non_ascii_characters(self):
        self.assertEqual(slugify('aåbäcö'), 'aaabaecoe')
        self.assertEqual(slugify(u'\u00BC'), '1/4')


class IterateTestCase(TestCase):
    def test_list(self):
        self.assertEqual(
            list(iterate([1, 2, 3])),
            [(None, 1), (None, 2), (None, 3)]
        )

    def test_tuple(self):
        self.assertEqual(
            list(iterate((1, 2, 3))),
            [(None, 1), (None, 2), (None, 3)]
        )

    def test_dict(self):
        self.assertEqual(
            list(iterate({'test': 1})),
            [('test', 1)]
        )

    def test_dict_with_nested_list(self):
        self.assertEqual(
            list(iterate({'test': [1, 2]})),
            [('test', 1), ('test', 2)]
        )

    def test_dict_with_nested_tuple(self):
        self.assertEqual(
            list(iterate({'test': (1, 2)})),
            [('test', 1), ('test', 2)]
        )

    def test_dict_with_nested_dict(self):
        self.assertEqual(
            list(iterate({'test': {'level1': 1}})),
            [('level1', 1)]
        )


class CompareInsensitiveTestCase(TestCase):
    def test_with_none(self):
        self.assertIsNone(compare_insensitive(None, 'A'))
        self.assertIsNone(compare_insensitive('A', None))

    def test_contains(self):
        self.assertTrue(compare_insensitive('ABC', 'ABC'))

    def test_does_not_contain(self):
        self.assertFalse(compare_insensitive('AB', 'ABC'))
