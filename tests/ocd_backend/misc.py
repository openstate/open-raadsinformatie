from unittest import TestCase
import datetime

from ocd_backend.utils.misc import normalize_motion_id

class MotionIdNormalizerTestCase(TestCase):
    def test_normalize_motion_id(self):
        year = datetime.datetime.now().isoformat()[0:4]
        normalized_motion_id = normalize_motion_id('2016 M 159')
        self.assertEqual(normalized_motion_id, '2016M159')
        normalized_motion_id = normalize_motion_id('2016 m 62')
        self.assertEqual(normalized_motion_id, '2016M62')
        normalized_motion_id = normalize_motion_id('M 124')
        self.assertEqual(normalized_motion_id, '%sM124' % year)
        normalized_motion_id = normalize_motion_id('M 124', '2016-05-26T00:00:00+02:00')
        self.assertEqual(normalized_motion_id, '2016M124')
        normalized_motion_id = normalize_motion_id('M2016-67')
        self.assertEqual(normalized_motion_id, '2016M67')
