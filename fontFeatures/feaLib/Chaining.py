# Code for converting a Chaining object into feaLib statements
import fontTools.feaLib.ast as feaast

def glyphref(g):
  if len(g) == 1:
    return feaast.GlyphName(g[0])
  return feaast.GlyphClass([feaast.GlyphName(x) for x in g])

def asFeaAST(self):
  # XXX - might be positioning, not substitution
  if len(self.lookups) > 0 and any([x is not None for x in self.lookups]):
    return feaast.ChainContextSubstStatement(
      [glyphref(x) for x in self.precontext],
      [glyphref(x) for x in self.input],
      [glyphref(x) for x in self.postcontext],
      self.lookups
    )
  else:
    return feaast.IgnoreSubstStatement(
    chainContexts=[[
      [glyphref(x) for x in self.precontext],
      [glyphref(x) for x in self.input],
      [glyphref(x) for x in self.postcontext]
    ]])

def asFea(self):
  return self.asFeaAST().asFea()
