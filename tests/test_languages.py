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

feature locl {
    script arab;
    language URD;
            lookupflag 0;
        ;
        sub a by b;

} locl;

feature locl {
    script arab;
    language FAR;
            lookupflag 0;
        ;
        sub a by c;

} locl;

feature locl {
    script arab;
    language URD;
            lookupflag 0;
        ;
        sub x y by z;

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
