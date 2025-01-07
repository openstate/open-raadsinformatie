import os

from unittest import TestCase

from ocd_backend.utils.file_parsing import parse_result_is_empty


class ParseResultIsEmptyTestCase(TestCase):
    def test_two_empty_pages(self):
        # two_empty_pages.md is actual output for toezeggingen_commissie_bme.pdf (Emmen)
        test_file = os.path.join(os.path.dirname(__file__), 'test_files/two_empty_pages.md')
        with open(test_file, 'r') as f:
            self.md_text = f.readlines()

        self.assertTrue(parse_result_is_empty(self.md_text))

    def test_non_empty_single_page(self):
        self.md_text = ["\nH\n"]
        self.assertFalse(parse_result_is_empty(self.md_text))

    def test_non_empty_page_among_multiple_empty_pages(self):
        self.md_text = ["---", "*%$##", "\nH\n", ""]
        self.assertFalse(parse_result_is_empty(self.md_text))

    def test_None(self):
        self.assertFalse(parse_result_is_empty(None))
