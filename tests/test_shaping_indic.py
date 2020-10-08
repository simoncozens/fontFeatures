from fontFeatures import FontFeatures
from fontFeatures.jankyPOS.Buffer import Buffer
from fontFeatures.fontProxy import FontProxy
from fontFeatures.shaperLib.Shaper import Shaper
from fontFeatures.ttLib import unparse
from fontTools.ttLib import TTFont
import pytest


test_data_glyphs = [  # fontname,string,serialization
    pytest.param(
        "1735326da89f0818cd8c51a0600e9789812c0f94.ttf",
        chr(0x0A51),
        "uni25CC+1044@<0,0>|udaatguru+0@<0,0>",
        id="gurumurki",
    ),
    pytest.param(
        "acbe26ce904463c690fb67f70679447059d13ee4.otf",
        "क्क",
        "dvK_KA+1284@<0,0>",
        id="virama_reordering",
    ),
    pytest.param(
        "acbe26ce904463c690fb67f70679447059d13ee4.otf",
        "क्क्क",
        "dvK+519@<0,0>|dvK_KA+1284@<0,0>",
        id="double_virama",
    ),
]


@pytest.mark.parametrize("fontname,string,serialization", test_data_glyphs)
def test_shaping(fontname, string, serialization):
    font = TTFont("tests/data/" + fontname)
    ff = unparse(font)
    buf = Buffer(FontProxy(font), unicodes=string)
    shaper = Shaper(ff, FontProxy(font))
    shaper.execute(buf)
    assert buf.serialize() == serialization


def test_shaping_matra_reorder():
    font = TTFont("tests/data/1735326da89f0818cd8c51a0600e9789812c0f94.ttf")
    ff = FontFeatures()
    buf = Buffer(FontProxy(font), unicodes="हि")
    shaper = Shaper(ff, FontProxy(font))
    shaper.execute(buf)
    # Force buffer to codepoints
    for i in buf.items:
        delattr(i, "glyph")
        delattr(i, "position")
    assert buf.serialize() == "U+093f|U+0939"
