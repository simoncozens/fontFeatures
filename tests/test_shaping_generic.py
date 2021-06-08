from fontFeatures import FontFeatures, Substitution, Routine
from fontFeatures.shaperLib.Buffer import Buffer
from fontFeatures.shaperLib.Shaper import Shaper
from babelfont import load
import pytest

@pytest.mark.skip("Font too broken to use")
def test_double_application():
    font = load("tests/data/acbe26ce904463c690fb67f70679447059d13ee4.otf" )
    buf = Buffer(font, glyphs=["dvKA","dvVirama","dvKA", "dvVirama", "dvKA"])
    rule = Substitution( [["dvKA"],["dvVirama"]], [["dvK"]] )
    rule.apply_to_buffer(buf)
    assert buf.serialize(position=False) == "dvK|dvK|dvKA"

def test_multiple_applications():
    font = load("tests/data/LibertinusSans-Regular.otf")
    buf = Buffer(font, glyphs=["A", "B", "C"])
    r = Routine()
    r.addRule( Substitution( [["A"]], [["X"]] ) )
    r.addRule( Substitution( [["B"]], [["Y"]] ) )
    r.apply_to_buffer(buf)
    assert buf.serialize(position=False) == "X|Y|C"


def test_namedclass_in_slot():
    font = load("tests/data/LibertinusSans-Regular.otf")
    buf = Buffer(font, glyphs=["A", "B", "C"])
    r = Routine()
    r.addRule( Substitution( [["G", "@AB"]], [["X"]] ) )
    r.apply_to_buffer(buf, namedclasses={"AB": ["A","B"]})
    assert buf.serialize(position=False) == "X|X|C"
