from fontFeatures import Positioning, ValueRecord
from lxml import etree

import unittest


class TestPositioning(unittest.TestCase):
    def roundTrip(self, thing):
        rt = thing.__class__.fromXML(thing.toXML())
        self.assertEqual(rt.asFea(), thing.asFea())

    def test_single(self):
        v = ValueRecord(xAdvance=120)
        s = Positioning(["a"], [v])
        self.assertEqual(s.asFea(), "pos a 120;")
        print(etree.tostring(s.toXML()))
        self.assertEqual(etree.tostring(s.toXML()), "<positioning><glyphs><slot><glyph>a</glyph></slot></glyphs><positions><valuerecord xAdvance=\"120\"/></positions></positioning>".encode("utf-8"))
        self.roundTrip(s)

    def test_single_class(self):
        v = ValueRecord(xPlacement=120)
        s = Positioning([["a", "b"]], [v])
        self.assertEqual(s.asFea(), "pos [a b] <120 0 0 0>;")

    def test_kern(self):
        v = ValueRecord(xAdvance=120)
        s = Positioning(["a", "b"], [v, ValueRecord()])
        self.assertEqual(s.asFea(), "pos a b 120;")
