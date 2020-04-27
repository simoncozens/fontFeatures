from fontFeatures import Substitution, Routine
from fontFeatures.optimizer import Optimizer

import unittest

class TestSubstitution(unittest.TestCase):
  def test_MergeMultipleSingleSubstitutions_1(self):
    r1 = Routine(rules = [
    	Substitution([["a","y"]], [["b","z"]]),
    	Substitution([["b","d","a"]], [["c","e","f"]]),
		 ] )
    Optimizer().optimize_routine(r1)
    self.assertEqual(r1.asFea(), "    sub [a y b d] by [c z c e];\n")

  def test_MergeMultipleSingleSubstitutions_2(self):
    r1 = Routine(rules = [
    	Substitution([["a"]], [["b"]]),
    	Substitution([["b"]], [["c"]]),
    	Substitution([["d"]], [["e"]]),
    	Substitution([["y"]], [["z"]]),
		 ] )
    Optimizer().optimize_routine(r1)
    self.assertEqual(r1.asFea(), "    sub [a b d y] by [c c e z];\n")
