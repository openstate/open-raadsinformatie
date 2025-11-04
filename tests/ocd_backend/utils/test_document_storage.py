from unittest import TestCase

from utils.pdf_naming import PdfNaming


class OriDocumentTestCase(TestCase):
    def test_normal_ids(self):
        self.assertEqual(PdfNaming._id_partitioned(345), '000/000/000')
        self.assertEqual(PdfNaming._id_partitioned(6930), '000/000/006')
        self.assertEqual(PdfNaming._id_partitioned(49630), '000/000/049')
        self.assertEqual(PdfNaming._id_partitioned(634291), '000/000/634')
        self.assertEqual(PdfNaming._id_partitioned(957241), '000/000/957')
        self.assertEqual(PdfNaming._id_partitioned(1000365), '000/001/000')
        self.assertEqual(PdfNaming._id_partitioned(1506895), '000/001/506')
        self.assertEqual(PdfNaming._id_partitioned(5849348398), '005/849/348')

    def test_edge_cases(self):
        self.assertEqual(PdfNaming._id_partitioned(1), '000/000/000')
        self.assertEqual(PdfNaming._id_partitioned(999), '000/000/000')
        self.assertEqual(PdfNaming._id_partitioned(1000), '000/000/001')
        self.assertEqual(PdfNaming._id_partitioned(1001), '000/000/001')
        self.assertEqual(PdfNaming._id_partitioned(2000), '000/000/002')
        self.assertEqual(PdfNaming._id_partitioned(2001), '000/000/002')
        self.assertEqual(PdfNaming._id_partitioned(999999), '000/000/999')
        self.assertEqual(PdfNaming._id_partitioned(1000000), '000/001/000')

        self.assertEqual(PdfNaming._id_partitioned(999999999), '000/999/999')
        self.assertEqual(PdfNaming._id_partitioned(1000000000), '001/000/000')
