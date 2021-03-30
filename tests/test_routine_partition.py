from fontFeatures import Substitution, FontFeatures, Routine, Chaining, RoutineReference

import pytest


def test_routine_partition():
    f = FontFeatures()

    s1 = Substitution([["A"]],  [["A.grk"]], languages=["grek/*"])
    s2 = Substitution([["A"]],  [["A.esp"]], languages=["latn/ESP "])
    r = Routine(rules=[s1,s2], flags=0x2)

    f.routines.append(r)

    dummy = Routine(rules=[Substitution([["G"]], [["G"]])])
    f.routines.append(dummy)

    c = Chaining([["A"], ["V"]], lookups=[
        [RoutineReference(routine=dummy), RoutineReference(routine=r)],
        [RoutineReference(routine=r), RoutineReference(routine=dummy)],
        ])
    r2 = Routine(rules=[c])
    f.routines.append(r2)

    f.addFeature("locl", [r])

    f.partitionRoutine(r, lambda rule: tuple(rule.languages or []))

    assert len(f.routines) == 4
    assert f.routines[0].flags == f.routines[1].flags
    assert len(f.routines[0].rules) == 1
    assert len(f.routines[1].rules) == 1
    assert f.routines[0].rules[0].replacement[0][0] == "A.grk"
    assert f.routines[1].rules[0].replacement[0][0] == "A.esp"

    assert len(c.lookups[0]) == 3
    assert len(f.features["locl"]) == 2



def test_routine_partition_not_needed():
    f = FontFeatures()

    s1 = Substitution([["A"]],  [["A.grk"]], languages=["grek/*"])
    s2 = Substitution([["A"]],  [["A.esp"]], languages=["grek/*"])
    r = Routine(rules=[s1,s2], flags=0x2)

    f.routines.append(r)
    f.partitionRoutine(r, lambda rule: tuple(rule.languages or []))

    assert len(f.routines) == 1

    r.rules = []
    f.partitionRoutine(r, lambda rule: tuple(rule.languages or []))
    assert len(f.routines) == 1
