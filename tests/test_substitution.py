from fontFeatures import Substitution

import unittest

class TestSubstitution(unittest.TestCase):
  def test_single(self):
    s = Substitution(["a"], ["b"])
    self.assertEqual(s.asFea(), "sub a by b;")

  def test_single_classes(self):
    s = Substitution([["a", "b"]], [["c", "d"]])
    self.assertEqual(s.asFea(), "sub [a b] by [c d];")

  def test_ligature(self):
    s = Substitution(["a", "b"], ["c"])
    self.assertEqual(s.asFea(), "sub a b by c;")

  def test_multiple(self):
    s = Substitution(["a"], ["b", "c"])
    self.assertEqual(s.asFea(), "sub a by b c;")

  def test_alternate(self):
    s = Substitution(["a"], [["b", "c"]])
    self.assertEqual(s.asFea(), "sub a from [b c];")
