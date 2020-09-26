from fontFeatures import Substitution
from lxml import etree

import unittest


class TestSubstitution(unittest.TestCase):
    def roundTrip(self, thing):
        rt = thing.__class__.fromXML(thing.toXML())
        self.assertEqual(rt.asFea(), thing.asFea())

    def test_single(self):
        s = Substitution(["a"], ["b"])
        self.assertEqual(s.asFea(), "sub a by b;")
        self.assertEqual(s.involved_glyphs, set(["a", "b"]))
        self.assertEqual(etree.tostring(s.toXML()), "<substitution><from><slot><glyph>a</glyph></slot></from><to><slot><glyph>b</glyph></slot></to></substitution>".encode("utf-8"))
        self.roundTrip(s)

    def test_single_classes(self):
        s = Substitution([["a", "b"]], [["c", "d"]])
        self.assertEqual(s.asFea(), "sub [a b] by [c d];")
        self.assertEqual(s.involved_glyphs, set(["a", "b", "c", "d"]))
        self.roundTrip(s)

    def test_ligature(self):
        s = Substitution(["a", "b"], ["c"])
        self.assertEqual(s.asFea(), "sub a b by c;")
        self.assertEqual(s.involved_glyphs, set(["a", "b", "c"]))
        self.roundTrip(s)

    def test_multiple(self):
        s = Substitution(["a"], ["b", "c"])
        self.assertEqual(s.asFea(), "sub a by b c;")
        self.assertEqual(s.involved_glyphs, set(["a", "b", "c"]))
        self.roundTrip(s)

    def test_alternate(self):
        s = Substitution(["a"], [["b", "c"]])
        self.assertEqual(s.asFea(), "sub a from [b c];")
        self.assertEqual(s.involved_glyphs, set(["a", "b", "c"]))
        self.roundTrip(s)
