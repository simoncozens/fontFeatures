from fontFeatures import Positioning, ValueRecord

import unittest


class TestPositioning(unittest.TestCase):
    def test_single(self):
        v = ValueRecord(xAdvance=120)
        s = Positioning(["a"], [v])
        self.assertEqual(s.asFea(), "pos a 120;")

    def test_single_class(self):
        v = ValueRecord(xPlacement=120)
        s = Positioning([["a", "b"]], [v])
        self.assertEqual(s.asFea(), "pos [a b] <120 0 0 0>;")

    def test_kern(self):
        v = ValueRecord(xAdvance=120)
        s = Positioning(["a", "b"], [v, ValueRecord()])
        self.assertEqual(s.asFea(), "pos a b 120;")
