import fontTools.feaLib.ast as feaast
from fontFeatures.ttLib.Positioning import lookup_type

def glyphref(g):
  if len(g) == 1:
    return feaast.GlyphName(g[0])
  return feaast.GlyphClass([feaast.GlyphName(x) for x in sorted(g)])

def asFeaAST(self):
  lut = lookup_type(self)
  glyphs = [glyphref(x) for x in self.glyphs]
  positionings = list(zip(glyphs, self.valuerecords))
  if lut == 1:
    return feaast.SinglePosStatement(
      positionings,
      [],
      [],
      False
    )
  if lut == 2:
    return feaast.PairPosStatement(
      glyphs[0],
      self.valuerecords[0],
      glyphs[1],
      self.valuerecords[1]
    )
  raise ValueError()
