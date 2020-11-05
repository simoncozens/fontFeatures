from fontFeatures import FontFeatures, Substitution
from fontFeatures.shaperLib.Buffer import Buffer
from fontFeatures.shaperLib.Shaper import Shaper
from babelfont import Babelfont
import pytest

@pytest.mark.skip("Font too broken to use")
def test_double_application():
    font = Babelfont.open("tests/data/acbe26ce904463c690fb67f70679447059d13ee4.otf" )
    buf = Buffer(font, glyphs=["dvKA","dvVirama","dvKA", "dvVirama", "dvKA"])
    rule = Substitution( [["dvKA"],["dvVirama"]], [["dvK"]] )
    rule.apply_to_buffer(buf)
    assert buf.serialize(position=False) == "dvK|dvK|dvKA"
