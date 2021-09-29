from fontFeatures import Substitution, FontFeatures
from fontTools.ttLib import TTFont
from fontFeatures.ttLib.GSUBUnparser import GSUBUnparser
from fontFeatures.ttLib import unparseLanguageSystems
import pprint
import unittest


class TestUnparse(unittest.TestCase):
    font = TTFont("fonts/Amiri-Regular.ttf")
    lookups = font["GSUB"].table.LookupList.Lookup
    ff = FontFeatures()
    unparser = GSUBUnparser(font["GSUB"], ff, [])

    def test_single(self):
        g, _ = self.unparser.unparseLookup(self.lookups[1], 1)  # part of locl
        self.assertEqual(g.rules[0].asFea(), "sub period by period.ara;")
        self.assertEqual(g.rules[1].asFea(), "sub guillemotleft by guillemotleft.ara;")

    def test_ligature(self):
        g, _ = self.unparser.unparseLookup(self.lookups[0], 0)  # part of ccmp
        self.assertEqual(g.rules[0].asFea(), "sub uni0627 uni065F by uni0673;")

    def test_multiple(self):
        g, _ = self.unparser.unparseLookup(self.lookups[10], 10)
        self.assertEqual(g.rules[0].asFea(), "sub uni08B6 by uni0628 smallmeem.above;")

    def test_ignore(self):
        g, _ = self.unparser.unparseLookup(self.lookups[47], 47)
        self.unparser.lookups = [None] * 47 + [g]
        assert self.unparser.lookups[47]
        g, _ = self.unparser.unparseLookup(self.lookups[48], 48)
        self.assertEqual(
            g.rules[0].asFea(),
            "ignore sub [uni0622 uni0627 uni0648 uni0671 uni0627.fina uni0671.fina] uni0644.init' uni0644.medi' [uni0647.fina uni06C1.fina];",
        )

    # def test_chaining(self):
    #     self.unparser.unparseLookups()
    #     g, _ = self.unparser.unparseLookup(
    #         self.lookups[33], 33
    #     )  # part of calt in quran.fea
    #     self.assertEqual(
    #         g.rules[0].asFea(),
    #         "sub uni0644' lookup SingleSubstitution32 uni0621' lookup SingleSubstitution31 uni0627' lookup SingleSubstitution32;",
    #     )
