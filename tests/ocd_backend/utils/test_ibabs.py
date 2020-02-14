from unittest import TestCase

from ocd_backend.utils.ibabs import translate_position


class TranslatePositionTestCase(TestCase):
    def test_castable_value(self):
        self.assertEqual(translate_position('1'), (1.0, None))
        self.assertEqual(translate_position('1.1'), (1.1, None))

    def test_uncastable_value(self):
        self.assertEqual(translate_position('1A'), (1.0, '1A'))
        self.assertEqual(translate_position('1.4C'), (1.4, '1.4C'))

    def test_untranslatable_value(self):
        self.assertEqual(translate_position('A'), (None, 'A'))
        self.assertEqual(translate_position('.'), (None, '.'))
