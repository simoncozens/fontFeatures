from fontFeatures.feeLib import FeeParser
from fontTools.ttLib import TTFont
from babelfont import Babelfont

import unittest
import re

class TestFeeDefinitions(unittest.TestCase):
    roboto = FeeParser(Babelfont.load("fonts/Roboto-Regular.ttf"))

    def assertSufficientlyEqual(self, s1, s2):
        def alltrim(a):
            a = re.sub("#.*", "", a)
            a = re.sub("\\s+", " ", a)
            return a.strip()

        self.assertEqual(alltrim(s1), alltrim(s2))

    def test_parse_to_ff(self):
        self.roboto.parseString("""
        	DefineClass @vowels = /^[aeiou]$/;
        	DefineClass @consonants = /^[bcdfghjklmnpqrstvwxyz]$/;
        	DefineClass @letters = [@vowels @consonants];
        	""");
        self.assertEqual(len(self.roboto.fontfeatures.namedClasses["letters"]),26)

    def test_unicode_range_selector(self):
        self.roboto.parseString("DefineClass @digits = U+0030=>U+0039;");
        self.assertEqual(len(self.roboto.fontfeatures.namedClasses["digits"]),10)
