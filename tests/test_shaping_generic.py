from fontFeatures import FontFeatures, Substitution
from fontFeatures.jankyPOS.Buffer import Buffer
from fontFeatures.fontProxy import FontProxy
from fontFeatures.shaperLib.Shaper import Shaper
from fontTools.ttLib import TTFont
import pytest

def test_double_application():
    font = TTFont("tests/data/acbe26ce904463c690fb67f70679447059d13ee4.otf" )
    buf = Buffer(font, glyphs=["dvKA","dvVirama","dvKA", "dvVirama", "dvKA"])
    rule = Substitution( [["dvKA"],["dvVirama"]], [["dvK"]] )
    rule.apply_to_buffer(buf)
    assert buf.serialize(position=False) == "dvK|dvK|dvKA"
