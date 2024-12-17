from unittest import TestCase

from ocd_backend.utils.pdf_storage import PdfStorage


class PdfStorageTestCase(TestCase):
    def test_tiny_id(self):
        self.assertEqual(PdfStorage.id_partitioned(5), '000/000/005')

    def test_small_id(self):
        self.assertEqual(PdfStorage.id_partitioned(847), '000/000/847')

    def test_medium_id(self):
        self.assertEqual(PdfStorage.id_partitioned(13823), '000/013/823')

    def test_large_id(self):
        self.assertEqual(PdfStorage.id_partitioned(431382623), '431/382/623')

    def test_too_large_id(self):
        self.assertEqual(PdfStorage.id_partitioned(2431382623), '243/138/2623')