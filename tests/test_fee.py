from fontFeatures.feeLib import FeeParser
from babelfont import Babelfont
from fontFeatures.shaperLib.Buffer import Buffer
from fontFeatures.shaperLib.Shaper import Shaper

import pytest
import os

@pytest.fixture
def parser():
    path, _ = os.path.split(__file__)
    fontpath = os.path.join(path, "data", "LibertinusSans-Regular.otf")
    return FeeParser(Babelfont.load(fontpath))


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
  Swap C { A B } E;
};
""")
    buf = Buffer(parser.font, unicodes="XABDCABDCABE")
    shaper = Shaper(parser.fontfeatures, parser.font)
    shaper.execute(buf)
    assert buf.serialize(position=False) == "X|A|B|D|C|A|B|D|C|B|A|E"

