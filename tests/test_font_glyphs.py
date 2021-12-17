import pytest
from fontTools.ttLib import TTFont
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontFeatures.fontGlyphs import FontGlyphs
import os


@pytest.fixture
def ttFont():
    path, _ = os.path.split(__file__)
    fontpath = os.path.join(path, "data", "LibertinusSans-Regular.otf")
    font = TTFont(fontpath)
    del font['GSUB']
    return font


def test_SingleSubstitution(ttFont):
    fea = """
        feature smcp {
            sub A by a.sc;
            sub B by b.sc;
        } smcp;
    """
    addOpenTypeFeaturesFromString(ttFont, fea)
    i = FontGlyphs(ttFont)
    i.inputs(features=["smcp"])
    assert i.glyph_inputs['a.sc'] == {'input': 'A', 'features': {'smcp'}}
    assert i.glyph_inputs['b.sc'] == {'input': 'B', 'features': {'smcp'}}


def test_SingleSubstitution2(ttFont):
    fea = """
    feature xxxx {
        sub A by a.sc;
        sub a.sc by b.sc;
        sub b.sc by c.sc;
    } xxxx;
    """
    addOpenTypeFeaturesFromString(ttFont, fea)
    i = FontGlyphs(ttFont)
    i.inputs(features=["xxxx"])
    assert i.glyph_inputs['c.sc'] == {'input': 'A', 'features': {'xxxx'}}


def test_MultipleSubstitution(ttFont):
    pass


def test_AlternateSubstitution(ttFont):
    pass


def test_LigatureSubstitution(ttFont):
    fea = """
        feature liga {
            sub f f by f_f;
        } liga;
    """
    addOpenTypeFeaturesFromString(ttFont, fea)
    i = FontGlyphs(ttFont)
    i.inputs()
    assert i.glyph_inputs['f_f'] == {'input': 'ff', 'features': {'liga'}}


def test_ContextualSubstitution_precontext(ttFont):
    fea = """
        feature ccmp {
            sub [a e n] h' by h.alt;
            sub [a o e] y' by y.alt;
        } ccmp;
    """
    addOpenTypeFeaturesFromString(ttFont, fea)
    i = FontGlyphs(ttFont)
    i.inputs()
    assert i.glyph_inputs['a-h'] == {'input': 'ah', 'features': {'ccmp'}}
    assert i.glyph_inputs['e-h'] == {'input': 'eh', 'features': {'ccmp'}}
    assert i.glyph_inputs['n-h'] == {'input': 'nh', 'features': {'ccmp'}}
    assert i.glyph_inputs['a-y'] == {'input': 'ay', 'features': {'ccmp'}}
    assert i.glyph_inputs['o-y'] == {'input': 'oy', 'features': {'ccmp'}}
    assert i.glyph_inputs['e-y'] == {'input': 'ey', 'features': {'ccmp'}}


def test_ContextualSubstitution_postcontext(ttFont):
    fea = """
        feature ccmp {
            sub h' [a e n] by h.alt;
            sub y' [a o e] by y.alt;
        } ccmp;
    """
    addOpenTypeFeaturesFromString(ttFont, fea)
    i = FontGlyphs(ttFont)
    i.inputs()
    assert i.glyph_inputs['h-a'] == {'input': 'ha', 'features': {'ccmp'}}
    assert i.glyph_inputs['h-e'] == {'input': 'he', 'features': {'ccmp'}}
    assert i.glyph_inputs['h-n'] == {'input': 'hn', 'features': {'ccmp'}}
    assert i.glyph_inputs['y-a'] == {'input': 'ya', 'features': {'ccmp'}}
    assert i.glyph_inputs['y-o'] == {'input': 'yo', 'features': {'ccmp'}}
    assert i.glyph_inputs['y-e'] == {'input': 'ye', 'features': {'ccmp'}}


def test_ContextualSubstitution_bothcontexts(ttFont):
    fea = """
        feature ccmp {
            sub a h' [e n] by h.alt;
            sub a y' [o e] by y.alt;
        } ccmp;
    """
    addOpenTypeFeaturesFromString(ttFont, fea)
    i = FontGlyphs(ttFont)
    i.inputs()
    assert i.glyph_inputs['a-h-e'] == {'input': 'ahe', 'features': {'ccmp'}}
    assert i.glyph_inputs['a-h-n'] == {'input': 'ahn', 'features': {'ccmp'}}
    assert i.glyph_inputs['a-y-o'] == {'input': 'ayo', 'features': {'ccmp'}}
    assert i.glyph_inputs['a-y-e'] == {'input': 'aye', 'features': {'ccmp'}}


def test_ConetextualSubstitution_with_lookups(ttFont):
    fea = """
        lookup CNTXT_LIGS {
        substitute c t by c_t;
    } CNTXT_LIGS;

    lookup CNTXT_SUB {
        substitute n by j;
        substitute s by j;
    } CNTXT_SUB;

    feature test {
        substitute [ a e i o u] c' lookup CNTXT_LIGS t' s' lookup CNTXT_SUB;
    } test;
    """
    addOpenTypeFeaturesFromString(ttFont, fea)
    i = FontGlyphs(ttFont)
    i.inputs(features=["test"])
    assert i.glyph_inputs['a-c-t-s'] == {'input': 'acts', 'features': {'test'}}
    assert i.glyph_inputs['e-c-t-s'] == {'input': 'ects', 'features': {'test'}}
    assert i.glyph_inputs['i-c-t-s'] == {'input': 'icts', 'features': {'test'}}
    assert i.glyph_inputs['o-c-t-s'] == {'input': 'octs', 'features': {'test'}}
    assert i.glyph_inputs['u-c-t-s'] == {'input': 'ucts', 'features': {'test'}}
