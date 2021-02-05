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

    def test_ligature_expansion(self):
        s = Substitution([["f", "f.ss01"], ["i", "i.ss01"]], [["f_i", "f_i.ss01"]])
        self.assertEqual(s.asFea(), "    sub f i by f_i;\n    sub f.ss01 i.ss01 by f_i.ss01;\n")
        self.assertEqual(s.involved_glyphs, set(["f", "i", "f_i", "f.ss01", "i.ss01", "f_i.ss01"]))
        self.roundTrip(s)

    def test_multiple(self):
        s = Substitution(["a"], ["b", "c"])
        self.assertEqual(s.asFea(), "sub a by b c;")
        self.assertEqual(s.involved_glyphs, set(["a", "b", "c"]))
        self.roundTrip(s)

    def test_multiple_expansion(self):
        s = Substitution([["a", "b"]], [["a", "b"], "c"])
        self.assertEqual(s.asFea(), "    sub a by a c;\n    sub b by b c;\n")
        self.assertEqual(s.involved_glyphs, set(["a", "b", "c"]))
        self.roundTrip(s)

    def test_multiple_expansion_middle(self):
        s = Substitution([["aa", "bb"]], ["d", ["aa", "bb"], "c"])
        self.assertEqual(s.asFea(), "    sub aa by d aa c;\n    sub bb by d bb c;\n")
        self.assertEqual(s.involved_glyphs, set(["aa", "bb", "c", "d"]))
        self.roundTrip(s)

    def test_alternate(self):
        s = Substitution(["a"], [["b", "c"]])
        self.assertEqual(s.asFea(), "sub a from [b c];")
        self.assertEqual(s.involved_glyphs, set(["a", "b", "c"]))
        self.roundTrip(s)
