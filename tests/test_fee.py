from fontFeatures.feeLib import FeeParser
from babelfont import load
from fontFeatures.shaperLib.Buffer import Buffer
from fontFeatures.shaperLib.Shaper import Shaper

import pytest
import os

path, _ = os.path.split(__file__)
fontpath = os.path.join(path, "data", "LibertinusSans-Regular.otf")
font = load(fontpath)

@pytest.fixture
def parser():
    return FeeParser(font)


def test_swap(parser):
    parser.parseString("""
LoadPlugin Swap;
Feature liga {
  Swap A B;
};
""")
    buf = Buffer(parser.font, unicodes="CABD")
    shaper = Shaper(parser.fontfeatures, parser.font)
    shaper.execute(buf)
    assert buf.serialize(position=False) == "C|B|A|D"




def test_swap2(parser):
    parser.parseString("""
LoadPlugin Swap;
Feature liga {
  Swap C ( A B ) E;
};
""")
    buf = Buffer(parser.font, unicodes="XABDCABDCABE")
    shaper = Shaper(parser.fontfeatures, parser.font)
    shaper.execute(buf)
    assert buf.serialize(position=False) == "X|A|B|D|C|A|B|D|C|B|A|E"



def test_chain(parser):
    parser.parseString("""
Routine a_to_b { Substitute A -> B; };
Feature liga {
  Chain X ( A ^a_to_b) Y;
};
""")
    buf = Buffer(parser.font, unicodes="XAYXAX")
    shaper = Shaper(parser.fontfeatures, parser.font)
    shaper.execute(buf)
    assert buf.serialize(position=False) == "X|B|Y|X|A|X"

