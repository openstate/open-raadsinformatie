from unittest import TestCase

from ocd_backend.transformers.parlaeus_meeting import clean_link

class ParlaeusMeetingTestCase(TestCase):
    def test_clean_link(self):
        url = "https://maastricht.parlaeus.nlhttps://maastricht.parlaeus.nl/user/postin/action=select/start=20241111/end=20241124/ty=262"
        clean_url = "https://maastricht.parlaeus.nl/user/postin/action=select/start=20241111/end=20241124/ty=262"
        self.assertEqual(clean_link(url), clean_url)

    def test_clean_link_skip(self):
        url = "https://maastricht.parlaeus.nl/user/postin/action=select/start=20241111/end=20241124/ty=262"
        self.assertEqual(clean_link(url), url)

    def test_clean_link_empty(self):
        self.assertEqual(clean_link(""), "")

    def test_clean_link_none(self):
        self.assertEqual(clean_link(None), None)
