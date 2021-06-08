from fontFeatures.feeLib import FeeParser, GlyphSelector, FEEVerb
from babelfont import load
import lark
from lark import Tree, Token
import pytest
import os
import re


def alltrim(a):
    a = re.sub("lookupflag 0;", "", a)
    a = re.sub("#.*", "", a)
    a = re.sub("\\s+", " ", a)
    a = re.sub("table GDEF.*GDEF;", "", a)
    return a.strip()

path, _ = os.path.split(__file__)
fontpath = os.path.join(path, "data", "LibertinusSans-Regular.otf")
font = load(fontpath)

@pytest.fixture
def parser():
    return FeeParser(font)

############
# BareName #
############

class BareNameModule:
    GRAMMAR = """
    ?start: action
    action: BARENAME
    """

    VERBS = ["BareName"]

    PARSEOPTS = dict(use_helpers=True)

    class BareName(FEEVerb):
        pass

def test_barename(parser):
    parser.register_plugin(BareNameModule, "BareName")

    def test_barename_string(test_bn):
        s = "BareName %s;" % test_bn
        a = parser.parseString(s)
        assert a == ("BareName", Tree('action', [Token('BARENAME', test_bn)]))

    test_barename_string("foo")
    test_barename_string("CH_YEf1")
    test_barename_string("teh-ar")

#############
# ClassName #
#############

class ClassNameModule:
    GRAMMAR = """
    ?start: action
    action: CLASSNAME
    """

    VERBS = ["ClassName"]

    PARSEOPTS = dict(use_helpers=True)

    class ClassName(FEEVerb):
        pass

def test_classname(parser):
    parser.register_plugin(ClassNameModule, "ClassName")

    def test_classname_string(test_bn):
        s = "ClassName %s;" % test_bn
        a = parser.parseString(s)
        assert a == ("ClassName", Tree('action', [Token('CLASSNAME', test_bn)]))

    test_classname_string("@foo")

###############
# InlineClass #
###############

class InlineClassModule:
    GRAMMAR = """
    ?start: action
    action: inlineclass
    """

    VERBS = ["InlineClass"]

    PARSEOPTS = dict(use_helpers=True)

    class InlineClass(FEEVerb):
        pass

def test_inlineclass(parser):
    s = "InlineClass [a b c @foo];"
    parser.register_plugin(InlineClassModule, "InlineClass")
    a = parser.parseString(s)
    assert a == ('InlineClass', Tree('action', [Token('INLINECLASS', [{'barename': 'a'}, {'barename': 'b'}, {'barename': 'c'}, {'classname': 'foo'}])]))

#################
# GlyphSelector #
#################

class GlyphSelectorModule:
    GRAMMAR = """
    ?start: action
    action: glyphselector
    """

    VERBS = ["GlyphSelector"]

    PARSEOPTS = dict(use_helpers=True)

    class GlyphSelector(FEEVerb):
        def action(self, args):
            return args


def test_glyphselector(parser):
    s = "[foo @bar].sc"
    stmt = "GlyphSelector %s;" % s
    parser.register_plugin(GlyphSelectorModule, "GlyphSelector")
    a = parser.parseString(stmt)
    _, (gs,) = a
    assert gs.as_text() == s

###############
# DefineClass #
###############

from fontFeatures.feeLib import ClassDefinition

class ConjunctionModule:
    GRAMMAR = ClassDefinition.GRAMMAR

    Conjunction_GRAMMAR = """
    ?start: conjunction
    """

    VERBS = ["Conjunction"]

    PARSEOPTS = dict(use_helpers=True)

    class Conjunction(ClassDefinition.DefineClass):
        pass

def test_classdefinition_conjunctions(parser):
    parser.register_plugin(ConjunctionModule, "Conjunction")
    s = "Conjunction A | B;"
    (_, a) = parser.parseString(s)
    assert isinstance(a, dict)
    assert a["conjunction"] == "or"
    assert a["left"] == ["A"]
    assert a["right"] == ["B"]

def test_classdefinition_with_conjunction(parser):
    s = """
    DefineClass @foo = /^[a-z]$/;
    DefineClass @bar = /^[g-o]\.sc$/;
    DefineClass @conjunction = @foo.sc & @bar;
    """
    parser.parseString(s)
    matches = set(["{}.sc".format(c) for c in "ghijklmno"])
    assert set(parser.fontfeatures.namedClasses["conjunction"]) == matches

def test_classdefinition_with_predicate(parser):
    s = r"DefineClass @foo = /\.sc$/ & (width > 500);"
    parser.parseString(s)
    assert len(parser.fontfeatures.namedClasses["foo"]) == 49

#################
# Substitutions #
#################

def test_substitute(parser):
    s = "Feature rlig { Substitute a -> b; };"
    parser.parseString(s)
    assert alltrim(parser.fontfeatures.asFea()) == alltrim(
        "feature rlig { lookup Routine_1 { ; sub a by b; } Routine_1; } rlig;"
    )


def test_substitute2(parser):
    s = "Feature rlig { Substitute [a b] -> [c d]; };"
    parser.parseString(s)
    assert alltrim(parser.fontfeatures.asFea()) == alltrim(
        "feature rlig { lookup Routine_1 { ; sub [a b] by [c d]; } Routine_1; } rlig;"
    )
