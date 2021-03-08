from fontFeatures.variableScalar import VariableScalar
from fontTools.designspaceLib import AxisDescriptor as Axis
from fontTools.varLib.varStore import OnlineVarStoreBuilder
from fontTools.misc.testTools import getXML

import pytest

axes = [
    Axis(tag="wght", minimum=200, maximum=1000, default=400),
    Axis(tag="wdth", minimum=100, maximum=300, default=300)
]


def test_varscalar():
    scalar = VariableScalar(axes)

    scalar.add_value({"wght": 200}, 5)
    with pytest.raises(ValueError):
      scalar.default

    scalar.add_value({"wght": 400}, 10)
    assert scalar.default == 10

    scalar.add_value({"wdth": 100, "wght": 400}, 12)
    assert scalar.default == 10

    assert scalar.value_at_location({"wght": 400, "wdth": 100}) == 12

    assert scalar.value_at_location({"wght": 400, "wdth": 200}) == 11
    assert scalar.value_at_location({"wdth": 200, "wght": 400}) == 11

    scalar.get_deltas_and_supports()

def test_storebuilder():
    sb = OnlineVarStoreBuilder([ax.tag for ax in axes])

    scalar = VariableScalar(axes)
    scalar.add_value({"wght": 200}, 5)
    scalar.add_value({"wght": 400}, 10)
    scalar.add_value({"wdth": 100, "wght": 400}, 12)
    default1, index1 = scalar.add_to_variation_store(sb)

    scalar2 = VariableScalar(axes)
    scalar2.add_value({"wght": 400}, 21)
    scalar2.add_value({"wght": 800}, 36)
    scalar2.add_value({"wght": 900, "wdth": 150}, 41)
    scalar2.add_value({"wght": 1000}, 47)
    scalar2.add_value({"wght": 1000, "wdth": 300}, 52)
    default2, index2 = scalar2.add_to_variation_store(sb)

    assert default1 == 10
    assert default2 == 21
    indirectStore = sb.finish()  # Test unoptimized version for debuggability
    storexml = "\n".join(getXML(indirectStore.toXML))
    assert storexml == """<VarStore Format="1">
  <Format value="1"/>
  <VarRegionList>
    <!-- RegionAxisCount=2 -->
    <!-- RegionCount=5 -->
    <Region index="0">
      <VarRegionAxis index="0">
        <StartCoord value="0.0"/>
        <PeakCoord value="0.0"/>
        <EndCoord value="0.0"/>
      </VarRegionAxis>
      <VarRegionAxis index="1">
        <StartCoord value="-1.0"/>
        <PeakCoord value="-1.0"/>
        <EndCoord value="0.0"/>
      </VarRegionAxis>
    </Region>
    <Region index="1">
      <VarRegionAxis index="0">
        <StartCoord value="-1.0"/>
        <PeakCoord value="-1.0"/>
        <EndCoord value="0.0"/>
      </VarRegionAxis>
      <VarRegionAxis index="1">
        <StartCoord value="0.0"/>
        <PeakCoord value="0.0"/>
        <EndCoord value="0.0"/>
      </VarRegionAxis>
    </Region>
    <Region index="2">
      <VarRegionAxis index="0">
        <StartCoord value="0.0"/>
        <PeakCoord value="0.6667"/>
        <EndCoord value="1.0"/>
      </VarRegionAxis>
      <VarRegionAxis index="1">
        <StartCoord value="0.0"/>
        <PeakCoord value="0.0"/>
        <EndCoord value="0.0"/>
      </VarRegionAxis>
    </Region>
    <Region index="3">
      <VarRegionAxis index="0">
        <StartCoord value="0.6667"/>
        <PeakCoord value="1.0"/>
        <EndCoord value="1.0"/>
      </VarRegionAxis>
      <VarRegionAxis index="1">
        <StartCoord value="0.0"/>
        <PeakCoord value="0.0"/>
        <EndCoord value="0.0"/>
      </VarRegionAxis>
    </Region>
    <Region index="4">
      <VarRegionAxis index="0">
        <StartCoord value="0.0"/>
        <PeakCoord value="0.8333"/>
        <EndCoord value="1.0"/>
      </VarRegionAxis>
      <VarRegionAxis index="1">
        <StartCoord value="-0.75"/>
        <PeakCoord value="-0.75"/>
        <EndCoord value="0.0"/>
      </VarRegionAxis>
    </Region>
  </VarRegionList>
  <!-- VarDataCount=2 -->
  <VarData index="0">
    <!-- ItemCount=1 -->
    <NumShorts value="0"/>
    <!-- VarRegionCount=2 -->
    <VarRegionIndex index="0" value="0"/>
    <VarRegionIndex index="1" value="1"/>
    <Item index="0" value="[2, -5]"/>
  </VarData>
  <VarData index="1">
    <!-- ItemCount=1 -->
    <NumShorts value="0"/>
    <!-- VarRegionCount=3 -->
    <VarRegionIndex index="0" value="2"/>
    <VarRegionIndex index="1" value="3"/>
    <VarRegionIndex index="2" value="4"/>
    <Item index="0" value="[15, 31, -3]"/>
  </VarData>
</VarStore>"""
