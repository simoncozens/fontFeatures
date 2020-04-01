# Code for converting a Substitution object into feaLib statements
import fontTools.feaLib.ast as feaast

def glyphref(g):
  if len(g) == 1:
    return feaast.GlyphName(g[0])
  return feaast.GlyphClass([feaast.GlyphName(x) for x in g])

def asFeaAST(self):
  if len(self.lookups) > 0 and any([x is not None for x in self.lookups]):
    return feaast.ChainContextSubstStatement(
      [glyphref(x) for x in self.precontext],
      [glyphref(x) for x in self.input],
      [glyphref(x) for x in self.postcontext],
      self.lookups
    )
  if self.input == self.replacement:
    return feaast.IgnoreSubstStatement(
    chainContexts=[[
      [glyphref(x) for x in self.precontext],
      [glyphref(x) for x in self.input],
      [glyphref(x) for x in self.postcontext]
    ]])
  if len(self.input) == 1 and len(self.replacement) == 1:
    if len(self.input[0]) == 1 and len(self.replacement[0]) > 1:
      return feaast.AlternateSubstStatement(
      [glyphref(x) for x in self.precontext],
      glyphref(self.input[0]),
      [glyphref(x) for x in self.postcontext],
      feaast.GlyphClass([feaast.GlyphName(x) for x in self.replacement[0]])
      )
    else:
      return feaast.SingleSubstStatement(
        [glyphref(x) for x in self.input],
        [glyphref(x) for x in self.replacement],
        [glyphref(x) for x in self.precontext],
        [glyphref(x) for x in self.postcontext],
        False
      )
  if len(self.input) > 1 and len(self.replacement) == 1:
    return feaast.LigatureSubstStatement(
      [glyphref(x) for x in self.precontext],
      [glyphref(x) for x in self.input],
      [glyphref(x) for x in self.postcontext],
      glyphref(self.replacement[0]),
      False
    )
  if len(self.replacement) > 1:
    return feaast.MultipleSubstStatement(
    [glyphref(x) for x in self.precontext],
    glyphref(self.input[0]),
    [glyphref(x) for x in self.postcontext],
    [glyphref(x) for x in self.replacement])

  if len(self.input) > 1 and len(self.replacement) > 1:
    # Now we have to get creative
    pass

  raise ValueError()

def asFea(self):
  return self.asFeaAST().asFea()
