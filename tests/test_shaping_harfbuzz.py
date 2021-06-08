from fontFeatures import FontFeatures
from fontFeatures.shaperLib.Buffer import Buffer
from fontFeatures.shaperLib.Shaper import Shaper
from fontFeatures.ttLib import unparse
from fontTools.ttLib import TTFont
from babelfont import load
import pytest
import glob
import os
import re
import logging

if "CI" in os.environ:
    pytest.skip("Not running shaping tests on CI", allow_module_level=True)

script_map = {
    "Qaag": "Myanmar_Zawgyi"
}

# logging.getLogger("fontFeatures.shaperLib").setLevel(logging.DEBUG)

def tounicode(s):
    out = ""
    for part in s.split(","):
        if part.startswith("U+"):
            part = part[2:]
        out = out + chr(int(part,16))
    return out

tests = []
for testfile in glob.glob("tests/harfbuzz/*/tests/*.tests"):
    filetests = open(testfile,"r").readlines()
    for ix, t in enumerate(filetests):
        t = t.rstrip()
        if not t:
            continue
        if t[0] == "#":
            continue
            # t = t[1:]
        testname = testfile[:-6] + "_" + str(ix) # ".tests"
        font, hb_args, buf, expectation = t.split(":")
        font = os.path.join(os.path.dirname(testfile), font)
        if not os.path.exists(font):
            continue
        tests.append(pytest.param(font,hb_args,buf,expectation, id=testname))


@pytest.mark.parametrize("fontname,hb_args,input_string,expectation", tests)
def test_shaping(request, fontname, hb_args, input_string, expectation):
    font = TTFont(fontname)
    ff = unparse(font)
    bbf = load(fontname)
    if not bbf:
        return pytest.skip("Font too busted to use")
    buf = Buffer(bbf, unicodes=tounicode(input_string))
    shaper = Shaper(ff, bbf)
    feature_string = ""
    if "[" in hb_args:
        return pytest.skip("Partial application not supported yet")

    if "variations" in hb_args:
        return pytest.skip("Not planning to support variations")
    if "ttb" in hb_args:
        return pytest.skip("Not planning to support top-to-bottom")

    if "rand" in request.node.name:
        return pytest.skip("Not planning to support rand feature")
    if "aat" in request.node.name:
        return pytest.skip("Not planning to support Apple Advanced Typography")
    if "kern-format2" in request.node.name:
        return pytest.skip("Not planning to support kern table")
    if "fraction" in request.node.name:
        return pytest.skip("Not planning to support automatic fractions")

    m = re.search(r'--features="([^"]+)"', hb_args)
    if m:
        feature_string = m[1]

    if "--script" in hb_args:
        m = re.search(r"--script=(\w+)", hb_args)
        buf.script = script_map[m[1]]

    shaper.execute(buf, features=feature_string)
    serialize_options = {}
    if "--no-glyph-names" in hb_args:
        serialize_options["names"] = False
    if "--ned" in hb_args:
        serialize_options["ned"] = True
    if "--no-position" in hb_args:
        serialize_options["position"] = False
    if "post" not in font or font["post"].formatType != 2.0:
        serialize_options["names"] = False
        expectation = re.sub("gid", "", expectation)
    serialized = buf.serialize(**serialize_options)

    # Finesse cluster information
    serialized = re.sub(r"=\d+", "", serialized)
    expectation = re.sub(r"=\d+", "", expectation)
    assert "["+serialized+"]" == expectation
