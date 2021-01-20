from fontFeatures import Substitution, Routine, FontFeatures
from fontFeatures.optimizer import Optimizer

import unittest
import pytest


pytest.skip("Optimizer is currently broken", allow_module_level=True)

class TestSubstitution(unittest.TestCase):
    def test_MergeMultipleSingleSubstitutions_1(self):
        r1 = Routine(
            rules=[
                Substitution([["a", "y"]], [["b", "z"]]),
                Substitution([["b", "d", "a"]], [["c", "e", "f"]]),
            ]
        )
        Optimizer(FontFeatures()).optimize_routine(r1, level=1)
        self.assertEqual(r1.asFea(), "    sub [a y b d] by [c z c e];\n")

    def test_MergeMultipleSingleSubstitutions_2(self):
        r1 = Routine(
            rules=[
                Substitution([["a"]], [["b"]]),
                Substitution([["b"]], [["c"]]),
                Substitution([["d"]], [["e"]]),
                Substitution([["y"]], [["z"]]),
            ]
        )
        Optimizer(FontFeatures()).optimize_routine(r1, level=1)
        self.assertEqual(r1.asFea(), "    sub [a b d y] by [c c e z];\n")

    def test_GlyphClasses(self):
        r1 = Routine(
            rules=[Substitution([["a", "b", "c", "d", "e", "f", "g", "h"]], [["z"]]),]
        )
        ff = FontFeatures()
        Optimizer(ff).optimize_routine(r1, level=1)
        self.assertEqual(r1.asFea(), "    sub @class1 by z;\n")
        self.assertEqual(
            ff.namedClasses["class1"], ("a", "b", "c", "d", "e", "f", "g", "h")
        )
