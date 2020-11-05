from fontFeatures.feeLib import FeeParser
from fontTools.ttLib import TTFont
from babelfont import Babelfont

import unittest
import re

class TestFeeDefinitions(unittest.TestCase):
    def assertSufficientlyEqual(self, s1, s2):
        def alltrim(a):
            a = re.sub("#.*", "", a)
            a = re.sub("\\s+", " ", a)
            return a.strip()

        self.assertEqual(alltrim(s1), alltrim(s2))

    def test_parse_to_ff(self):
        p = FeeParser(Babelfont.open("fonts/Roboto-Regular.ttf"))
        p.parseString("""
        	DefineClass @vowels = /^[aeiou]$/;
        	DefineClass @consonants = /^[bcdfghjklmnpqrstvwxyz]$/;
        	DefineClass @letters = [@vowels @consonants];
        	""");
        self.assertEqual(len(p.fontfeatures.namedClasses["letters"]),26)
