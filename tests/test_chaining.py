from fontFeatures import Chaining, Positioning, ValueRecord, Routine, Substitution, RoutineReference, FontFeatures
from lxml import etree


import unittest


class TestChaining(unittest.TestCase):
    def roundTrip(self, thing, dependencies):
        f = FontFeatures()
        f.routines.extend(dependencies)
        rt = thing.__class__.fromXML(thing.toXML())
        f.routines.append(Routine(rules=[rt]))
        f.resolveAllRoutines()
        self.assertEqual(rt.asFea(), thing.asFea())

    def test_simple_pos(self):
        v = ValueRecord(xAdvance=120)
        pos = Positioning(["a"], [v])
        r = Routine(rules=[pos], name="dummy")
        rr = RoutineReference(routine=r)

        c = Chaining([["a"], ["b"]], lookups=[[rr], None])
        self.assertEqual(c.asFea(), "pos a' lookup dummy b';")
        xml = c.toXML()
        self.assertEqual(etree.tostring(xml), '<chaining><lookups><slot><routinereference name="dummy"/></slot><slot><lookup/></slot></lookups><input><slot><glyph>a</glyph></slot><slot><glyph>b</glyph></slot></input></chaining>'.encode("utf-8"))
        self.roundTrip(c, [r])

    def test_simple_sub(self):
        pos = Substitution(["a"], ["b"])
        r = Routine(rules=[pos], name="dummy")
        rr = RoutineReference(routine=r)

        c = Chaining([["a"], ["b"]], lookups=[[rr], None])
        self.assertEqual(c.asFea(), "sub a' lookup dummy b';")

    def test_ignore(self):
        c = Chaining([["a"], ["b"]], lookups=[])
        self.assertEqual(c.asFea(), "ignore sub a b;")

    def test_complex(self):
        pos1 = Substitution(["a"], ["b"])
        pos2 = Substitution(["b"], ["c"])
        r1 = Routine(rules=[pos1], name="dummy1")
        r2 = Routine(rules=[pos2], name="dummy2")
        rr1 = RoutineReference(routine=r1)
        rr2 = RoutineReference(routine=r2)

        c = Chaining([["a"], ["b"]], lookups=[[rr1, rr2], None])
        self.assertEqual(c.asFea(), "sub a' lookup dummy1 lookup dummy2 b';")

    def test_complex_pos(self):
        v = ValueRecord(xAdvance=120)
        pos1 = Positioning(["a"], [v])
        r1 = Routine(rules=[pos1])
        rr1 = RoutineReference(routine=r1)

        c = Chaining([["a"], ["b"]], lookups=[[rr1], None])
        c.feaPreamble(FontFeatures())
        self.assertEqual(c.asFea(), "pos a' lookup ChainedRoutine1 b';")

