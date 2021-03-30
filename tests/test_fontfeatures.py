from fontFeatures import FontFeatures, Routine


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

    combined = f1 + f2
    assert combined.namedClasses["One"] == ["A", "B", "C"]
    assert combined.namedClasses["Two"] == ["d", "e", "f"]
    assert "onex" in combined.features
    assert combined.features["onex"][0].routine == r1
    assert "twox" in combined.features
    assert combined.features["twox"][0].routine == r2
    assert combined.glyphclasses["a"] == "base"
    assert combined.glyphclasses["d"] == "mark"

def test_routine_named():
    r1 = Routine(name="One")
    f1 = FontFeatures()
    f1.addFeature("onex", [r1])
    assert f1.routineNamed("One") == r1
