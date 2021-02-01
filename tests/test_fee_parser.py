from fontFeatures.feeLib import FeeParser, GlyphSelector
import fontFeatures.feeLib.ClassDefinition as DefineClass
from ometa.builder import writePython
from ometa.grammar import OMeta
from babelfont import Babelfont
import pytest
import os
import re


def alltrim(a):
    a = re.sub("lookupflag 0;", "", a)
    a = re.sub("#.*", "", a)
    a = re.sub("\\s+", " ", a)
    a = re.sub("table GDEF.*GDEF;", "", a)
    return a.strip()


@pytest.fixture
def parser():
    path, _ = os.path.split(__file__)
    fontpath = os.path.join(path, "data", "LibertinusSans-Regular.otf")
    return FeeParser(Babelfont.load(fontpath))


def test_barename(parser):
    s = "foo"
    a = parser.parser(s).barename()
    assert a == {"barename": s}

    s = "CH_YEf1"
    a = parser.parser(s).barename()
    assert a == {"barename": s}

    s = "teh-ar"
    a = parser.parser(s).barename()
    assert a == {"barename": s}


def test_classname(parser):
    s = "@foo"
    a = parser.parser(s).classname()
    assert a == {"classname": "foo"}


def test_inlineclass(parser):
    s = "[a b c @foo]"
    a = parser.parser(s).inlineclass()
    assert a == {
        "inlineclass": [
            {"barename": "a"},
            {"barename": "b"},
            {"barename": "c"},
            {"classname": "foo"},
        ]
    }


def test_glyphselector(parser):
    s = "[foo @bar].sc"
    a = parser.parser(s).glyphselector()
    assert a.as_text() == s


def test_classdefinition_conjunctions(parser):
    s = "foo | bar"
    a = parser.grammar.globals["DefineClass"](s).apply("primary")[0]
    assert isinstance(a, dict)
    assert a["conjunction"] == "or"
    assert a["left"].as_text() == "foo"
    assert a["right"].as_text() == "bar"

    s = "@foo.sc & @bar~sc"
    a = parser.grammar.globals["DefineClass"](s).apply("primary")[0]
    assert isinstance(a, dict)
    assert a["conjunction"] == "and"
    assert a["left"].as_text() == "@foo.sc"
    assert a["right"].as_text() == "@bar~sc"


def test_classdefinition_with_predicate(parser):
    s = "(@foo | @bar) and (width <= 200)"
    a = parser.grammar.globals["DefineClass"](s).apply("definition")[0]
    assert isinstance(a[0], dict)
    assert isinstance(a[1], list)

    s = "@foo = /\\.sc$/ and (width > 500)"
    a = parser.grammar.globals["DefineClass"](s).apply("DefineClass_Args")[0]

    s = "DefineClass @foo = /\\.sc$/ and (width > 500);"
    parser.parser(s).statement()
    assert len(parser.fontfeatures.namedClasses["foo"]) == 49


def test_substitute(parser):
    s = "Feature rlig { Substitute a -> b; };"
    parser.parser(s).feefile()
    assert alltrim(parser.fontfeatures.asFea()) == alltrim(
        "feature rlig { lookup Routine_1 { ; sub a by b; } Routine_1; } rlig;"
    )


def test_substitute2(parser):
    s = "Feature rlig { Substitute [a b] -> [c d]; };"
    parser.parser(s).feefile()
    assert alltrim(parser.fontfeatures.asFea()) == alltrim(
        "feature rlig { lookup Routine_1 { ; sub [a b] by [c d]; } Routine_1; } rlig;"
    )
