from fontFeatures import Substitution
from fontFeatures.feaLib import FeaParser

import pytest

import re

def assertSufficientlyEqual(s1, s2):
    def alltrim(a):
        a = re.sub("lookupflag 0;", "", a)
        a = re.sub("#.*", "", a)
        a = re.sub("\\s+", " ", a)
        a = re.sub("table GDEF.*GDEF;", "", a)
        a = re.sub(" ; ", " ", a)
        return a.strip()

    assert alltrim(s1) == alltrim(s2)

@pytest.mark.parametrize("s", [
    # pytest.param("lookup dummy { } dummy;", id="single_dummy"),
    # pytest.param("lookup dummy1 { } dummy1; lookup dummy2 { } dummy2;", id="double_dummy"),
    pytest.param("lookup dummy { sub a by b; } dummy;", id="single_subst"),
    pytest.param("lookup dummy { sub x a' y by b; } dummy;", id="single_marked_subst"),
    pytest.param("lookup dummy { sub [a b] by [d e]; } dummy;", id="single_group_subst"),
    pytest.param("lookup dummy { sub [a b]' y by [d e]; } dummy;", id="single_marked_group_subst"),
    pytest.param("lookup dummy { sub one two [a b]' y by [d e]; } dummy;", id="single_prepost_1"),
    pytest.param("lookup dummy { sub [one two] [a b]' y by [d e]; } dummy;", id="single_prepost_2"),
    pytest.param("lookup dummy { sub f_f_i by f f i; } dummy;", id="decomposition"),
    pytest.param("lookup dummy { sub f_f_i' x by f f i; } dummy;", id="decomposition_marked"),
    pytest.param("lookup dummy { sub [a b] f_f_i' x by f f i; } dummy;", id="decomposition_context"),
    pytest.param("lookup dummy { sub ampersand from [ampersand.1 ampersand.2 ampersand.3]; } dummy;", id="alternate"),
    pytest.param("lookup dummy { sub x ampersand' from [ampersand.1 ampersand.2 ampersand.3]; } dummy;", id="contextual_alternate"),
    pytest.param("lookup dummy { sub [one one.oldstyle] [slash fraction] [two two.oldstyle] by onehalf; } dummy;",id="fraction"),
    pytest.param("lookup dummy { sub [o u] f' f' by f_f; } dummy;",id="marked_ligature"),
    pytest.param("lookup dummy { sub [e e.begin]' t' c by ampersand; } dummy;",id="contextual"),
    pytest.param("lookup dummy { sub a by b; } dummy; lookup chain { sub a' lookup dummy; } chain; ",id="chain"),
    pytest.param("lookup dummy { sub a by b; } dummy; lookup chain { sub x [one two] a' lookup dummy b' lookup dummy; } chain; ",id="chain2"),
    pytest.param("lookup dummy { rsub a b' c by d; } dummy; ",id="rsub"),
    pytest.param("lookup dummy { ignore sub a d' d; } dummy; ",id="ignore"),
    pytest.param("lookup a { sub a by b; sub c by d; } a; feature calt { lookup a; } calt;",id="feature"),
    pytest.param("lookup dummy { pos one <-80 0 -160 0>; } dummy;",id="pos_one"),
    pytest.param("lookup dummy { pos [one two] <-80 0 -160 0>; } dummy;",id="pos_one_group"),
    pytest.param("lookup dummy { pos a [one two]' <-80 0 -160 0>; } dummy;",id="pos_one_contexual"),
    pytest.param("lookup dummy { pos s f' 10 t; } dummy;",id="pos_one_contextual_alt_format"),
    pytest.param("lookup dummy { pos T -60 a <-40 0 -40 0>; } dummy;",id="pos_two"),
    pytest.param("lookup dummy { pos [X Y] -60 a <-40 0 -40 0>; } dummy;",id="pos_two_group"),
    pytest.param("lookup dummy { pos T a -100; } dummy;",id="pos_two_one_null"),
    pytest.param("lookup dummy { pos cursive meem.medial <anchor 500 20> <anchor 0 -20>; } dummy;",id="pos_cursive1"),
    pytest.param("lookup dummy { pos cursive meem.init <anchor NULL> <anchor 0 -20>; } dummy;",id="pos_cursive2"),
    pytest.param(
        """markClass [acute grave] <anchor 150 -10> @TOP_MARKS;
  lookup dummy {
  pos base [a e o u] <anchor 250 450> mark @TOP_MARKS;
  } dummy;
  """, id="mark_attachment"
        ),
    pytest.param("lookup dummy { pos X [A B]' -40 B' -40 A' -40 Y; } dummy;", id="pos_contextual"),
    # pytest.param("lookup dummy { sub a b by c; } dummy; feature calt { lookup dummy; } calt;", id="lookup_reference"),
    pytest.param("lookup dummy { lookupflag IgnoreMarks; sub a b by c; } dummy;", id="lookup_flag"),
    # pytest.param("feature calt { lookupflag IgnoreMarks; sub a b by c; } calt;", id="flag_in_feature"),
    # pytest.param("feature calt { sub x by y; lookupflag IgnoreMarks; sub a b by c; } calt;", id="switch_flags"),
])
def test_round_trip(s):
    parser = FeaParser(s)
    parser.parse()
    assertSufficientlyEqual(parser.ff.asFea(), s)

# Mark to mark
# Mark to lig
# Ignore pos
# Languages
