from fontFeatures import Substitution

import unittest


class TestSubstitution(unittest.TestCase):
    def test_single(self):
        s = Substitution(["a"], ["b"])
        self.assertEqual(s.asFea(), "sub a by b;")
        self.assertEqual(s.involved_glyphs, set(["a", "b"]))

    def test_single_classes(self):
        s = Substitution([["a", "b"]], [["c", "d"]])
        self.assertEqual(s.asFea(), "sub [a b] by [c d];")
        self.assertEqual(s.involved_glyphs, set(["a", "b", "c", "d"]))

    def test_ligature(self):
        s = Substitution(["a", "b"], ["c"])
        self.assertEqual(s.asFea(), "sub a b by c;")
        self.assertEqual(s.involved_glyphs, set(["a", "b", "c"]))

    def test_multiple(self):
        s = Substitution(["a"], ["b", "c"])
        self.assertEqual(s.asFea(), "sub a by b c;")
        self.assertEqual(s.involved_glyphs, set(["a", "b", "c"]))

    def test_alternate(self):
        s = Substitution(["a"], [["b", "c"]])
        self.assertEqual(s.asFea(), "sub a from [b c];")
        self.assertEqual(s.involved_glyphs, set(["a", "b", "c"]))
