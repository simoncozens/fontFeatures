from fontFeatures.fontDameLib import unparse
import re


def assertSufficientlyEqual(s1, s2):
    def alltrim(a):
        a = re.sub("lookupflag 0;", "", a)
        a = re.sub("#.*", "", a)
        a = re.sub("\\s+", " ", a)
        a = re.sub("table GDEF.*GDEF;", "", a)
        a = re.sub(" ; ", " ", a)
        return a.strip()

    assert alltrim(s1) == alltrim(s2)


def test_noto_sharada():
    ff = unparse("tests/data/Noto Sans Sharada GSUB.txt")
    assert "abvs" in ff.features
    assert "akhn" in ff.features
    assert "blws" in ff.features
    assert len(ff.routines) == 12
    r1 = ff.features["abvs"][0].routine.asFea()
    assertSufficientlyEqual(r1, """
    sub Jihvamuliya by Jihvamuliya.ns;
    sub Upadhmaniya by Upadhmaniya.ns;
""")
    r2 = ff.features["blws"][1].routine.asFea()
    assertSufficientlyEqual(r2, """
sub [KKa NgKa RKa RGa JNya TtKa NnSha Sa]' [U UU]' lookup lookup_9;
sub [KKa NgKa RKa RGa JNya TtKa NnSha Sa]' [UU.alt U.alt]' lookup lookup_9;
sub [KTa RTa U UU]' [U UU]' lookup lookup_11;
sub [KTa RTa U UU]' [UU.alt U.alt]' lookup lookup_11;
sub [KKa NgKa RKa RGa JNya TtKa NnSha Sa]' [KTa RTa U UU]' lookup lookup_10;
""")

