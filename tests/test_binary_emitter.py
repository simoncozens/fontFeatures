from fontFeatures import Substitution, FontFeatures, Routine, Chaining, RoutineReference
from fontFeatures.feaLib import FeaParser
from fontTools.ttLib import TTFont
import pytest
from fontTools.misc.testTools import getXML


font = TTFont("fonts/Roboto-Regular.ttf")


def test_script_language_split():
    f = FontFeatures()

    s1 = Substitution([["question"]],  [["questiongreek"]], languages=[ ("grek","*") ])
    s2 = Substitution([["A"]],  [["alpha"]], languages=[ ("grek","ELL ") ])
    s3 = Substitution([["question"]],  [["questiondown"]], languages=[ ("latn", "ESP ") ])
    s4 = Substitution([["question"]],  [["B"]], languages=[ ("latn", "POL ") ])
    s5 = Substitution([["X"]],  [["Y"]])
    r = Routine(rules=[s1,s2,s3,s4,s5])

    f.addFeature("locl", [r])
    f.buildBinaryFeatures(font)
    gsub = "\n".join(getXML(font["GSUB"].toXML))
    assert gsub == """<Version value="0x00010000"/>
<ScriptList>
  <!-- ScriptCount=3 -->
  <ScriptRecord index="0">
    <ScriptTag value="DFLT"/>
    <Script>
      <DefaultLangSys>
        <ReqFeatureIndex value="65535"/>
        <!-- FeatureCount=1 -->
        <FeatureIndex index="0" value="3"/>
      </DefaultLangSys>
      <!-- LangSysCount=0 -->
    </Script>
  </ScriptRecord>
  <ScriptRecord index="1">
    <ScriptTag value="grek"/>
    <Script>
      <DefaultLangSys>
        <ReqFeatureIndex value="65535"/>
        <!-- FeatureCount=1 -->
        <FeatureIndex index="0" value="4"/>
      </DefaultLangSys>
      <!-- LangSysCount=1 -->
      <LangSysRecord index="0">
        <LangSysTag value="ELL "/>
        <LangSys>
          <ReqFeatureIndex value="65535"/>
          <!-- FeatureCount=1 -->
          <FeatureIndex index="0" value="0"/>
        </LangSys>
      </LangSysRecord>
    </Script>
  </ScriptRecord>
  <ScriptRecord index="2">
    <ScriptTag value="latn"/>
    <Script>
      <DefaultLangSys>
        <ReqFeatureIndex value="65535"/>
        <!-- FeatureCount=1 -->
        <FeatureIndex index="0" value="3"/>
      </DefaultLangSys>
      <!-- LangSysCount=2 -->
      <LangSysRecord index="0">
        <LangSysTag value="ESP "/>
        <LangSys>
          <ReqFeatureIndex value="65535"/>
          <!-- FeatureCount=1 -->
          <FeatureIndex index="0" value="1"/>
        </LangSys>
      </LangSysRecord>
      <LangSysRecord index="1">
        <LangSysTag value="POL "/>
        <LangSys>
          <ReqFeatureIndex value="65535"/>
          <!-- FeatureCount=1 -->
          <FeatureIndex index="0" value="2"/>
        </LangSys>
      </LangSysRecord>
    </Script>
  </ScriptRecord>
</ScriptList>
<FeatureList>
  <!-- FeatureCount=5 -->
  <FeatureRecord index="0">
    <FeatureTag value="locl"/>
    <Feature>
      <!-- LookupCount=3 -->
      <LookupListIndex index="0" value="0"/>
      <LookupListIndex index="1" value="1"/>
      <LookupListIndex index="2" value="4"/>
    </Feature>
  </FeatureRecord>
  <FeatureRecord index="1">
    <FeatureTag value="locl"/>
    <Feature>
      <!-- LookupCount=2 -->
      <LookupListIndex index="0" value="2"/>
      <LookupListIndex index="1" value="4"/>
    </Feature>
  </FeatureRecord>
  <FeatureRecord index="2">
    <FeatureTag value="locl"/>
    <Feature>
      <!-- LookupCount=2 -->
      <LookupListIndex index="0" value="3"/>
      <LookupListIndex index="1" value="4"/>
    </Feature>
  </FeatureRecord>
  <FeatureRecord index="3">
    <FeatureTag value="locl"/>
    <Feature>
      <!-- LookupCount=1 -->
      <LookupListIndex index="0" value="4"/>
    </Feature>
  </FeatureRecord>
  <FeatureRecord index="4">
    <FeatureTag value="locl"/>
    <Feature>
      <!-- LookupCount=2 -->
      <LookupListIndex index="0" value="0"/>
      <LookupListIndex index="1" value="4"/>
    </Feature>
  </FeatureRecord>
</FeatureList>
<LookupList>
  <!-- LookupCount=5 -->
  <Lookup index="0">
    <LookupType value="1"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <SingleSubst index="0">
      <Substitution in="question" out="questiongreek"/>
    </SingleSubst>
  </Lookup>
  <Lookup index="1">
    <LookupType value="1"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <SingleSubst index="0">
      <Substitution in="A" out="alpha"/>
    </SingleSubst>
  </Lookup>
  <Lookup index="2">
    <LookupType value="1"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <SingleSubst index="0">
      <Substitution in="question" out="questiondown"/>
    </SingleSubst>
  </Lookup>
  <Lookup index="3">
    <LookupType value="1"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <SingleSubst index="0">
      <Substitution in="question" out="B"/>
    </SingleSubst>
  </Lookup>
  <Lookup index="4">
    <LookupType value="1"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <SingleSubst index="0">
      <Substitution in="X" out="Y"/>
    </SingleSubst>
  </Lookup>
</LookupList>"""


def test_different_sub_types():
    parser = FeaParser("""
lookup single { sub a by b; } single;
lookup single_flags { lookupflag IgnoreMarks; sub a by b; } single_flags;
lookup multiple { sub a by b c; } multiple;
lookup ligature { sub a b by c; } ligature;
lookup chain1 { sub a b' by c; } chain1;
lookup rsub { rsub a b' c by d; } rsub;
lookup chain2 { sub a' lookup single_flags b; } chain2;
""")
    parser.parse()
    parser.ff.buildBinaryFeatures(font)
    gsub = "\n".join(getXML(font["GSUB"].toXML))
    assert gsub == """<Version value="0x00010000"/>
<ScriptList>
  <!-- ScriptCount=0 -->
</ScriptList>
<FeatureList>
  <!-- FeatureCount=0 -->
</FeatureList>
<LookupList>
  <!-- LookupCount=8 -->
  <Lookup index="0">
    <LookupType value="1"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <SingleSubst index="0">
      <Substitution in="a" out="b"/>
    </SingleSubst>
  </Lookup>
  <Lookup index="1">
    <LookupType value="1"/>
    <LookupFlag value="8"/><!-- ignoreMarks -->
    <!-- SubTableCount=1 -->
    <SingleSubst index="0">
      <Substitution in="a" out="b"/>
    </SingleSubst>
  </Lookup>
  <Lookup index="2">
    <LookupType value="2"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <MultipleSubst index="0">
      <Substitution in="a" out="b,c"/>
    </MultipleSubst>
  </Lookup>
  <Lookup index="3">
    <LookupType value="4"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <LigatureSubst index="0">
      <LigatureSet glyph="a">
        <Ligature components="b" glyph="c"/>
      </LigatureSet>
    </LigatureSubst>
  </Lookup>
  <Lookup index="4">
    <LookupType value="1"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <SingleSubst index="0">
      <Substitution in="b" out="c"/>
    </SingleSubst>
  </Lookup>
  <Lookup index="5">
    <LookupType value="6"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <ChainContextSubst index="0" Format="3">
      <!-- BacktrackGlyphCount=1 -->
      <BacktrackCoverage index="0">
        <Glyph value="a"/>
      </BacktrackCoverage>
      <!-- InputGlyphCount=1 -->
      <InputCoverage index="0">
        <Glyph value="b"/>
      </InputCoverage>
      <!-- LookAheadGlyphCount=0 -->
      <!-- SubstCount=1 -->
      <SubstLookupRecord index="0">
        <SequenceIndex value="0"/>
        <LookupListIndex value="4"/>
      </SubstLookupRecord>
    </ChainContextSubst>
  </Lookup>
  <Lookup index="6">
    <LookupType value="8"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <ReverseChainSingleSubst index="0" Format="1">
      <Coverage>
        <Glyph value="b"/>
      </Coverage>
      <!-- BacktrackGlyphCount=1 -->
      <BacktrackCoverage index="0">
        <Glyph value="a"/>
      </BacktrackCoverage>
      <!-- LookAheadGlyphCount=1 -->
      <LookAheadCoverage index="0">
        <Glyph value="c"/>
      </LookAheadCoverage>
      <!-- GlyphCount=1 -->
      <Substitute index="0" value="d"/>
    </ReverseChainSingleSubst>
  </Lookup>
  <Lookup index="7">
    <LookupType value="6"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <ChainContextSubst index="0" Format="3">
      <!-- BacktrackGlyphCount=0 -->
      <!-- InputGlyphCount=1 -->
      <InputCoverage index="0">
        <Glyph value="a"/>
      </InputCoverage>
      <!-- LookAheadGlyphCount=1 -->
      <LookAheadCoverage index="0">
        <Glyph value="b"/>
      </LookAheadCoverage>
      <!-- SubstCount=1 -->
      <SubstLookupRecord index="0">
        <SequenceIndex value="0"/>
        <LookupListIndex value="1"/>
      </SubstLookupRecord>
    </ChainContextSubst>
  </Lookup>
</LookupList>"""

def test_different_pos_types():
    parser = FeaParser("""
markClass [acute grave] <anchor 150 -10> @TOP_MARKS;
lookup single { pos a 50; } single;
lookup pair_and_class_pair { pos a 20 b 50; pos [a b] 15 c 10; } pair_and_class_pair;
lookup cursive { pos cursive c <anchor 500 200> <anchor 0 0>; } cursive;
lookup markbase { position base [a b] <anchor 250 450> mark @TOP_MARKS; } markbase;
lookup markmark { position mark [dieresis] <anchor 20 40> mark @TOP_MARKS; } markmark;
lookup chain1 { pos a' 50 b; } chain1;
lookup chain2 { pos a' lookup single b; } chain2;
""")
    parser.parse()
    parser.ff.glyphclasses["dieresis"] = "mark"
    parser.ff.buildBinaryFeatures(font)
    gpos = "\n".join(getXML(font["GPOS"].toXML))
    assert gpos == """<Version value="0x00010000"/>
<ScriptList>
  <!-- ScriptCount=0 -->
</ScriptList>
<FeatureList>
  <!-- FeatureCount=0 -->
</FeatureList>
<LookupList>
  <!-- LookupCount=8 -->
  <Lookup index="0">
    <LookupType value="1"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <SinglePos index="0" Format="1">
      <Coverage>
        <Glyph value="a"/>
      </Coverage>
      <ValueFormat value="4"/>
      <Value XAdvance="50"/>
    </SinglePos>
  </Lookup>
  <Lookup index="1">
    <LookupType value="2"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=2 -->
    <PairPos index="0" Format="1">
      <Coverage>
        <Glyph value="a"/>
      </Coverage>
      <ValueFormat1 value="4"/>
      <ValueFormat2 value="4"/>
      <!-- PairSetCount=1 -->
      <PairSet index="0">
        <!-- PairValueCount=1 -->
        <PairValueRecord index="0">
          <SecondGlyph value="b"/>
          <Value1 XAdvance="20"/>
          <Value2 XAdvance="50"/>
        </PairValueRecord>
      </PairSet>
    </PairPos>
    <PairPos index="1" Format="2">
      <Coverage>
        <Glyph value="a"/>
        <Glyph value="b"/>
      </Coverage>
      <ValueFormat1 value="4"/>
      <ValueFormat2 value="4"/>
      <ClassDef1>
      </ClassDef1>
      <ClassDef2>
        <ClassDef glyph="c" class="1"/>
      </ClassDef2>
      <!-- Class1Count=1 -->
      <!-- Class2Count=2 -->
      <Class1Record index="0">
        <Class2Record index="0">
          <Value1 XAdvance="0"/>
          <Value2 XAdvance="0"/>
        </Class2Record>
        <Class2Record index="1">
          <Value1 XAdvance="15"/>
          <Value2 XAdvance="10"/>
        </Class2Record>
      </Class1Record>
    </PairPos>
  </Lookup>
  <Lookup index="2">
    <LookupType value="3"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <CursivePos index="0" Format="1">
      <Coverage>
        <Glyph value="c"/>
      </Coverage>
      <!-- EntryExitCount=1 -->
      <EntryExitRecord index="0">
        <EntryAnchor Format="1">
          <XCoordinate value="500"/>
          <YCoordinate value="200"/>
        </EntryAnchor>
        <ExitAnchor Format="1">
          <XCoordinate value="0"/>
          <YCoordinate value="0"/>
        </ExitAnchor>
      </EntryExitRecord>
    </CursivePos>
  </Lookup>
  <Lookup index="3">
    <LookupType value="4"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <MarkBasePos index="0" Format="1">
      <MarkCoverage>
        <Glyph value="grave"/>
        <Glyph value="acute"/>
      </MarkCoverage>
      <BaseCoverage>
        <Glyph value="a"/>
        <Glyph value="b"/>
      </BaseCoverage>
      <!-- ClassCount=1 -->
      <MarkArray>
        <!-- MarkCount=2 -->
        <MarkRecord index="0">
          <Class value="0"/>
          <MarkAnchor Format="1">
            <XCoordinate value="150"/>
            <YCoordinate value="-10"/>
          </MarkAnchor>
        </MarkRecord>
        <MarkRecord index="1">
          <Class value="0"/>
          <MarkAnchor Format="1">
            <XCoordinate value="150"/>
            <YCoordinate value="-10"/>
          </MarkAnchor>
        </MarkRecord>
      </MarkArray>
      <BaseArray>
        <!-- BaseCount=2 -->
        <BaseRecord index="0">
          <BaseAnchor index="0" Format="1">
            <XCoordinate value="250"/>
            <YCoordinate value="450"/>
          </BaseAnchor>
        </BaseRecord>
        <BaseRecord index="1">
          <BaseAnchor index="0" Format="1">
            <XCoordinate value="250"/>
            <YCoordinate value="450"/>
          </BaseAnchor>
        </BaseRecord>
      </BaseArray>
    </MarkBasePos>
  </Lookup>
  <Lookup index="4">
    <LookupType value="6"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <MarkMarkPos index="0" Format="1">
      <Mark1Coverage>
        <Glyph value="grave"/>
        <Glyph value="acute"/>
      </Mark1Coverage>
      <Mark2Coverage>
        <Glyph value="dieresis"/>
      </Mark2Coverage>
      <!-- ClassCount=1 -->
      <Mark1Array>
        <!-- MarkCount=2 -->
        <MarkRecord index="0">
          <Class value="0"/>
          <MarkAnchor Format="1">
            <XCoordinate value="150"/>
            <YCoordinate value="-10"/>
          </MarkAnchor>
        </MarkRecord>
        <MarkRecord index="1">
          <Class value="0"/>
          <MarkAnchor Format="1">
            <XCoordinate value="150"/>
            <YCoordinate value="-10"/>
          </MarkAnchor>
        </MarkRecord>
      </Mark1Array>
      <Mark2Array>
        <!-- Mark2Count=1 -->
        <Mark2Record index="0">
          <Mark2Anchor index="0" Format="1">
            <XCoordinate value="20"/>
            <YCoordinate value="40"/>
          </Mark2Anchor>
        </Mark2Record>
      </Mark2Array>
    </MarkMarkPos>
  </Lookup>
  <Lookup index="5">
    <LookupType value="1"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <SinglePos index="0" Format="1">
      <Coverage>
        <Glyph value="a"/>
      </Coverage>
      <ValueFormat value="4"/>
      <Value XAdvance="50"/>
    </SinglePos>
  </Lookup>
  <Lookup index="6">
    <LookupType value="8"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <ChainContextPos index="0" Format="3">
      <!-- BacktrackGlyphCount=0 -->
      <!-- InputGlyphCount=1 -->
      <InputCoverage index="0">
        <Glyph value="a"/>
      </InputCoverage>
      <!-- LookAheadGlyphCount=1 -->
      <LookAheadCoverage index="0">
        <Glyph value="b"/>
      </LookAheadCoverage>
      <!-- PosCount=1 -->
      <PosLookupRecord index="0">
        <SequenceIndex value="0"/>
        <LookupListIndex value="5"/>
      </PosLookupRecord>
    </ChainContextPos>
  </Lookup>
  <Lookup index="7">
    <LookupType value="8"/>
    <LookupFlag value="0"/>
    <!-- SubTableCount=1 -->
    <ChainContextPos index="0" Format="3">
      <!-- BacktrackGlyphCount=0 -->
      <!-- InputGlyphCount=1 -->
      <InputCoverage index="0">
        <Glyph value="a"/>
      </InputCoverage>
      <!-- LookAheadGlyphCount=1 -->
      <LookAheadCoverage index="0">
        <Glyph value="b"/>
      </LookAheadCoverage>
      <!-- PosCount=1 -->
      <PosLookupRecord index="0">
        <SequenceIndex value="0"/>
        <LookupListIndex value="0"/>
      </PosLookupRecord>
    </ChainContextPos>
  </Lookup>
</LookupList>"""
