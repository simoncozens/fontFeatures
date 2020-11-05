from fontFeatures import FontFeatures
from fontFeatures.shaperLib.Buffer import Buffer
from fontFeatures.shaperLib.Shaper import Shaper
from fontFeatures.ttLib import unparse
from fontTools.ttLib import TTFont
from babelfont import Babelfont
import pytest


def tounicode(s):
    out = ""
    for part in s.split(","):
        if part.startswith("U+"):
            part = part[2:]
        out = out + chr(int(part,16))
    return out

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
    pytest.param(
        "a014549f766436cf55b2ceb40e462038938ee899.ttf",
        chr(0x0CF1)+chr(0x0C95),
        "uni0CF1+1129@<0,0>|uni0C95_uni0CCD.blwf+358@<0,0>",
        id="indic_consonant_with_stacker1",
    ),
    pytest.param(
        "55c88ebbe938680b08f92c3de20713183e0c7481.ttf",
        chr(0x0CF2)+chr(0x0CAA),
        "uni0CF2+1539@<0,0>|uni0CAA_uni0CCD.blwf+245@<0,0>",
        id="indic_consonant_with_stacker2",
    ),
    pytest.param(
        "341421e629668b1a1242245d39238ca48432d35d.ttf",
        chr(0x0CF1),
        "uni0CF1+1129@<0,0>",
        id="indic_consonant_with_stacker3",
    ),
    pytest.param(
        "663aef6b019dbf45ffd74089e2b5f2496ceceb18.ttf",
        chr(0x0CF2),
        "uni0CF2+1539@<0,0>",
        id="indic_consonant_with_stacker4",
    ),
    # Skipped because broken font
    # pytest.param(
    #     "932ad5132c2761297c74e9976fe25b08e5ffa10b.ttf",
    #     tounicode("U+09DC,U+0020,U+09DD,U+0020,U+09A1,U+09BC,U+0020,U+09A2,U+09BC"),
    #     "bn_rha|space|bn_yya|space|bn_dda|bn_nukta|space|bn_ddha|bn_nukta",
    #     id="indic_decompose",
    # ),
    pytest.param(
        "1a3d8f381387dd29be1e897e4b5100ac8b4829e1.ttf",
        tounicode("U+09AC,U+09C7,U+09AC,U+09C7"),
        "uni09C7.init+273@<0,0>|uni09AC+460@<0,0>|uni09C7+307@<0,0>|uni09AC+460@<0,0>",
        id="indic_init",
    ),
]


@pytest.mark.parametrize("fontname,string,serialization", test_data_glyphs)
def test_shaping(fontname, string, serialization):
    font = TTFont("tests/data/" + fontname)
    ff = unparse(font)
    bbf = Babelfont.open("tests/data/" + fontname)
    buf = Buffer(bbf, unicodes=string)
    shaper = Shaper(ff, bbf)
    shaper.execute(buf)
    assert buf.serialize() == serialization


def test_shaping_matra_reorder():
    fontname = "1735326da89f0818cd8c51a0600e9789812c0f94.ttf"
    font = TTFont("tests/data/" + fontname)
    ff = FontFeatures()
    bbf = Babelfont.open("tests/data/" + fontname)
    buf = Buffer(bbf, unicodes="हि")
    shaper = Shaper(ff, bbf)
    shaper.execute(buf)
    # Force buffer to codepoints
    for i in buf.items:
        delattr(i, "glyph")
        delattr(i, "position")
    assert buf.serialize() == "U+093f|U+0939"
