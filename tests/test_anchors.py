from fontFeatures import Attachment, FontFeatures
from lxml import etree
import re

import unittest

def assertSufficientlyEqual(s1, s2):
    def alltrim(a):
        a = re.sub("lookupflag 0;", "", a)
        a = re.sub("#.*", "", a)
        a = re.sub("\\s+", " ", a)
        a = re.sub("table GDEF.*GDEF;", "", a)
        a = re.sub(" ; ", " ", a)
        return a.strip()

    assert alltrim(s1) == alltrim(s2)


class TestAnchors(unittest.TestCase):
    def roundTrip(self, thing):
      rt = thing.__class__.fromXML(thing.toXML())
      self.assertEqual(rt.asFea(), thing.asFea())

    def test_markbase(self):
        s = Attachment("top", "top_", {"A": (679, 1600)}, {"acutecomb": (-570, 1290)})
        assertSufficientlyEqual(s.asFea(), "    pos base A <anchor 679 1600> mark @top;\n")
        self.assertEqual(s.involved_glyphs, set(["A", "acutecomb"]))
        self.assertEqual(etree.tostring(s.toXML()), '<attachment basename="top" markname="top_"><base name="A" anchorX="679" anchorY="1600"/><mark name="acutecomb" anchorX="-570" anchorY="1290"/></attachment>'.encode("utf-8"))
        self.roundTrip(s)
