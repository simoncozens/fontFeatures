from fontFeatures import Substitution, FontFeatures, Routine

import pytest


def test_language_ordering():
    f = FontFeatures()
    s1 = Substitution([["a"]], ["b"], languages=[("arab", "URD ")])
    s2 = Substitution([["a"]], ["c"], languages=[("arab", "FAR ")])
    s3 = Substitution([["x"], ["y"]], ["z"], languages=[("arab", "URD ")])

    f.addFeature("locl", [Routine(rules=[ s1, s2, s3 ] )])

    # When going to fea, we put everything in its own feature block to
    # avoid stupid problems with language systems
    expected = """languagesystem arab URD;
languagesystem arab FAR;

lookup Routine_1 {
    lookupflag 0;
    ;
    sub a by b;
} Routine_1;

lookup Routine_2 {
    lookupflag 0;
    ;
    sub a by c;
} Routine_2;

lookup Routine_3 {
    lookupflag 0;
    ;
    sub x y by z;
} Routine_3;

feature locl {
    script arab;
    language URD;
            lookup Routine_1;

} locl;

feature locl {
    script arab;
    language FAR;
            lookup Routine_2;

} locl;

feature locl {
    script arab;
    language URD;
            lookup Routine_3;

} locl;
"""
    assert f.asFea(do_gdef=False) == expected

    # But the same is true of multiple lookups in the same feature
    f = FontFeatures()
    r1 = Routine(rules=[ s1 ])
    r2 = Routine(rules=[ s2 ])
    r3 = Routine(rules=[ s3 ])

    f.addFeature("locl", [r1,r2,r3])
    assert f.asFea(do_gdef=False) == expected


def test_multiple_languages():
    f = FontFeatures()
    s1 = Substitution([["a"]], ["b"], languages=[("arab", "URD "),("arab", "FAR ")])
    expected = """languagesystem arab URD;
languagesystem arab FAR;

lookup Routine_1 {
    lookupflag 0;
    ;
    sub a by b;
} Routine_1;

lookup Routine_2 {
    lookupflag 0;
    ;
    sub a by b;
} Routine_2;

feature locl {
    script arab;
    language URD;
            lookup Routine_1;

} locl;

feature locl {
    script arab;
    language FAR;
            lookup Routine_2;

} locl;
"""
    f = FontFeatures()
    r1 = Routine(rules=[ s1 ])
    f.addFeature("locl", [r1])
    assert f.asFea(do_gdef=False) == expected

def test_multiple_languages_routine():
    f = FontFeatures()
    s1 = Substitution([["a"]], ["b"])
    expected = """languagesystem arab URD;
languagesystem arab FAR;

lookup Routine_1 {
    lookupflag 0;
    ;
    sub a by b;
} Routine_1;

feature locl {
    script arab;
    language URD;
            lookup Routine_1;

} locl;

feature locl {
    script arab;
    language FAR;
            lookup Routine_1;

} locl;
"""
    f = FontFeatures()
    r1 = Routine(rules=[ s1 ], languages=[("arab", "URD "),("arab", "FAR ")])
    f.addFeature("locl", [r1])
    assert f.asFea(do_gdef=False) == expected

