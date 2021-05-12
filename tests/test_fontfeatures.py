from fontFeatures import FontFeatures, Routine
from lxml import etree
import re


expected = """
    <fontfeatures>
        <namedclasses>
            <class name="One">
                <glyph>A</glyph>
                <glyph>B</glyph>
                <glyph>C</glyph>
            </class>
            <class name="Two">
                <glyph>d</glyph>
                <glyph>e</glyph>
                <glyph>f</glyph>
            </class>
        </namedclasses>
        <routines>
            <routine name="One"/>
            <routine name="Two"/>
        </routines>
        <features>
            <feature name="onex">
                <routinereference name="One"/>
            </feature>
            <feature name="twox">
                <routinereference name="Two"/>
            </feature>
        </features>
        <anchors>
            <glyph name="a">
                <anchor name="top" x="300" y="200"/>
            </glyph>
        </anchors>
        <glyphclasses>
            <glyph name="a" class="base"/>
            <glyph name="d" class="mark"/>
        </glyphclasses>
    </fontfeatures>"""
expected = re.sub(r"(?m)^\s+", "", expected).replace("\n", "")


def test_add():
    r1 = Routine(name="One")
    r2 = Routine(name="Two")
    f1 = FontFeatures()
    f2 = FontFeatures()
    f1.namedClasses["One"] = ["A", "B", "C"]
    f1.glyphclasses["a"] = "base"
    f1.addFeature("onex", [r1])
    f2.namedClasses["Two"] = ["d", "e", "f"]
    f2.addFeature("twox", [r2])
    f2.glyphclasses["d"] = "mark"
    f2.anchors["a"] = { "top": (300, 200) }

    combined = f1 + f2
    assert combined.namedClasses["One"] == ["A", "B", "C"]
    assert combined.namedClasses["Two"] == ["d", "e", "f"]
    assert "onex" in combined.features
    assert combined.features["onex"][0].routine == r1
    assert "twox" in combined.features
    assert combined.features["twox"][0].routine == r2
    assert combined.glyphclasses["a"] == "base"
    assert combined.glyphclasses["d"] == "mark"

    el = combined.toXML()
    assert etree.tostring(el).decode() == expected

def test_fromXML():
    ff = FontFeatures.fromXML(etree.fromstring(expected))
    assert ff.namedClasses["One"] == ["A", "B", "C"]
    assert ff.namedClasses["Two"] == ["d", "e", "f"]
    assert "onex" in ff.features
    assert ff.features["onex"][0].routine == ff.routines[0]
    assert "twox" in ff.features
    assert ff.features["twox"][0].routine == ff.routines[1]
    assert ff.glyphclasses["a"] == "base"
    assert ff.glyphclasses["d"] == "mark"
    assert ff.anchors["a"] == { "top": (300, 200) }


def test_routine_named():
    r1 = Routine(name="One")
    f1 = FontFeatures()
    f1.addFeature("onex", [r1])
    assert f1.routineNamed("One") == r1
