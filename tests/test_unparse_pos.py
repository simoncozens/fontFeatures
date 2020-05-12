from fontFeatures import Substitution, FontFeatures
from fontTools.ttLib import TTFont
from fontFeatures.ttLib.GPOSUnparser import GPOSUnparser
from fontFeatures.ttLib import unparseLanguageSystems
import pprint
import unittest


class TestUnparse(unittest.TestCase):
    font = TTFont("fonts/Amiri-Regular.ttf")
    lookups = font["GPOS"].table.LookupList.Lookup
    unparser = GPOSUnparser(font["GPOS"], None, [])
    unparser.font = font

    def test_single_f1(self):
        g, _ = self.unparser.unparseLookup(self.lookups[1], 1)  # part of kern
        self.assertEqual(g.rules[0].asFea(), "pos uni0621.float <-146 0 0 0>;")

    def test_single_f1_class(self):
        g, _ = self.unparser.unparseLookup(self.lookups[3], 3)  # part of kern
        self.assertEqual(
            g.rules[0].asFea(),
            "pos [uni0627.fina uni0627.fina_KafMemAlf uni0627.fina_MemAlfFina uni0627.fina_Wide] <122 0 122 0>;",
        )

    def test_single_f2(self):
        g, _ = self.unparser.unparseLookup(
            self.lookups[3], 3
        )  # lookups called in mark feature
        self.assertEqual(g.rules[1].asFea(), "pos uni0627 <73 0 146 0>;")
        self.assertEqual(g.rules[2].asFea(), "pos uni06E5.low <24 0 122 0>;")

    def test_pair_f1(self):
        g, _ = self.unparser.unparseLookup(
            self.lookups[56], 56
        )  # proportional digits in kern feature
        self.assertEqual(g.rules[0].asFea(), "pos uni0660.prop uni0667.prop 24;")
        self.assertEqual(g.rules[1].asFea(), "pos uni0660.prop uni0668.prop 24;")

    def test_pair_f2(self):
        g, _ = self.unparser.unparseLookup(self.lookups[76], 76)  # kerns
        self.assertEqual(
            g.rules[0].asFea(),
            "pos [zero zero.prop] [A Aacute Abreve Acircumflex Adieresis Agrave Amacron Aogonek Aring Atilde] -10;",
        )
        self.assertEqual(
            g.rules[1].asFea(),
            "pos [zero zero.prop] [Y Yacute Ycircumflex Ydieresis Ygrave] -21;",
        )

    # def test_pair(self):
    #   g,_ = self.unparser.unparseLookup(self.lookups[56])
    #   self.assertEqual(g.rules[0].asFea(),"pos uni0621.float <-146 0 0 0>;")
