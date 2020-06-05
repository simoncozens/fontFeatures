from fontFeatures import Chaining, Positioning, ValueRecord, Routine, Substitution


import unittest


class TestChaining(unittest.TestCase):
    def test_simple_pos(self):
        v = ValueRecord(xAdvance=120)
        pos = Positioning(["a"], [v])
        r = Routine(rules=[pos], name="dummy")

        c = Chaining([["a"], ["b"]], lookups=[[r], None])
        self.assertEqual(c.asFea(), "pos a' lookup dummy b';")

    def test_simple_sub(self):
        pos = Substitution(["a"], ["b"])
        r = Routine(rules=[pos], name="dummy")

        c = Chaining([["a"], ["b"]], lookups=[[r], None])
        self.assertEqual(c.asFea(), "sub a' lookup dummy b';")

    def test_ignore(self):
        c = Chaining([["a"], ["b"]], lookups=[])
        self.assertEqual(c.asFea(), "ignore sub a b;")

    def test_complex(self):
        pos1 = Substitution(["a"], ["b"])
        pos2 = Substitution(["b"], ["c"])
        r1 = Routine(rules=[pos1], name="dummy1")
        r2 = Routine(rules=[pos2], name="dummy2")

        c = Chaining([["a"], ["b"]], lookups=[[r1, r2], None])
        self.assertEqual(c.asFea(), "sub a' lookup dummy1 lookup dummy2 b';")
