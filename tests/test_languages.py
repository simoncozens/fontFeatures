from fontFeatures.feeLib import FeeParser
from babelfont import load
from fontFeatures.shaperLib.Buffer import Buffer
from fontFeatures.shaperLib.Shaper import Shaper
from fontFeatures import FontFeatures, Substitution, Routine

import pytest
import os

path, _ = os.path.split(__file__)
fontpath = os.path.join(path, "data", "LibertinusSans-Regular.otf")
font = load(fontpath)
import re

@pytest.fixture
def parser():
    return FeeParser(font)

def test_fftofea_languages():
    ff = FontFeatures()
    sub1 = Substitution([["a"]], [["A"]], languages=[("arab", "dflt"), ("arab","URD ")])
    sub2 = Substitution([["b"]], [["B"]], languages=[("latn", "dflt")])
    routine = Routine(rules=[sub1,sub2])
    ff.addFeature("liga", [routine])
    print(ff.asFea())
    assert re.search(r"script arab;\s+language URD;[^}]+sub a by A;", ff.asFea())


def test_feetofea_languages(parser):
      parser.parseString("""
Feature liga {
   Substitute a -> A <<arab/dflt arab/URD>>;
   Substitute b -> B <<latn/dflt>>;
};
""")
      assert re.search(r"script arab;\s+language URD;[^}]+sub a by A;", parser.fontfeatures.asFea())
