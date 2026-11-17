"""unparse() output must not depend on PYTHONHASHSEED (issue #75)."""

import os
import subprocess
import sys
import unittest

from fontFeatures import Attachment, Chaining
from fontFeatures.ttLib.GTableUnparser import GTableUnparser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UNPARSE_CURSIVE = """
from fontTools.ttLib import TTFont
from fontFeatures.ttLib.GPOSUnparser import GPOSUnparser

font = TTFont("fonts/Amiri-Regular.ttf")
unparser = GPOSUnparser(font["GPOS"], None, [])
unparser.font = font
lookup = font["GPOS"].table.LookupList.Lookup[57]
routine, _ = unparser.unparseLookup(lookup, 57)
print(routine.asFea())
"""


class FakeFont:
    def __init__(self, glyph_order):
        self.glyph_order = glyph_order

    def getGlyphOrder(self):
        return self.glyph_order


class TestHashSeed(unittest.TestCase):
    def test_cursive_rules_in_insertion_order(self):
        rule = Attachment(
            "cursive_entry",
            "cursive_exit",
            {"c": (0, 0), "a": (10, 0)},
            {"a": (20, 0), "b": (30, 0)},
        )
        self.assertEqual(
            [line.strip() for line in rule.asFea().splitlines()],
            [
                "pos cursive c <anchor 0 0> <anchor NULL>;",
                "pos cursive a <anchor 10 0> <anchor 20 0>;",
                "pos cursive b <anchor NULL> <anchor 30 0>;",
            ],
        )

    def test_cursive_unparse_same_for_any_hash_seed(self):
        outputs = []
        for seed in ["1", "2"]:
            env = dict(os.environ, PYTHONHASHSEED=seed)
            outputs.append(
                subprocess.run(
                    [sys.executable, "-c", UNPARSE_CURSIVE],
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
            )
        self.assertIn("pos cursive", outputs[0])
        self.assertEqual(outputs[0], outputs[1])

    def test_class_0_in_glyph_order(self):
        font = FakeFont([".notdef", "a", "b", "c", "d"])
        classes = GTableUnparser._invertClassDef(None, {"b": 1, "d": 2}, font)
        self.assertEqual(classes, {1: ["b"], 2: ["d"], 0: [".notdef", "a", "c"]})

    def test_one_glyph_class_0_in_context(self):
        font = FakeFont([".notdef", "a", "b"])
        classes = GTableUnparser._invertClassDef(None, {"a": 1, "b": 1}, font)
        rule = Chaining([["a"]], postcontext=[classes[0]], lookups=[None])
        self.assertEqual(rule.asFea(), "ignore sub a' .notdef;")
