from fontFeatures import Chaining, Positioning, ValueRecord, Routine, Substitution
from lxml import etree


import unittest


class TestChaining(unittest.TestCase):
    def roundTrip(self, thing):
        rt = thing.__class__.fromXML(thing.toXML())
        self.assertEqual(rt.asFea(), thing.asFea())

    def test_simple_pos(self):
        v = ValueRecord(xAdvance=120)
        pos = Positioning(["a"], [v])
        r = Routine(rules=[pos], name="dummy")

        c = Chaining([["a"], ["b"]], lookups=[[r], None])
        self.assertEqual(c.asFea(), "pos a' lookup dummy b';")
        self.assertEqual(etree.tostring(c.toXML()), '<chaining><lookups><slot><routine name="dummy"><positioning><glyphs><slot><glyph>a</glyph></slot></glyphs><positions><valuerecord xAdvance="120"/></positions></positioning></routine></slot><slot><lookup/></slot></lookups><input><slot><glyph>a</glyph></slot><slot><glyph>b</glyph></slot></input></chaining>'.encode("utf-8"))

    def test_simple_sub(self):
        pos = Substitution(["a"], ["b"])
        r = Routine(rules=[pos], name="dummy")

        c = Chaining([["a"], ["b"]], lookups=[[r], None])
        self.assertEqual(c.asFea(), "sub a' lookup dummy b';")

    def test_ignore(self):
        c = Chaining([["a"], ["b"]], lookups=[])
        self.assertEqual(c.asFea(), "ignore sub a b;")

    def test_complex(self):
        pos1 = Substitution(["a"], ["b"])
        pos2 = Substitution(["b"], ["c"])
        r1 = Routine(rules=[pos1], name="dummy1")
        r2 = Routine(rules=[pos2], name="dummy2")

        c = Chaining([["a"], ["b"]], lookups=[[r1, r2], None])
        self.assertEqual(c.asFea(), "sub a' lookup dummy1 lookup dummy2 b';")
