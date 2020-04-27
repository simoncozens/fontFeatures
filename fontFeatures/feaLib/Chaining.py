# Code for converting a Chaining object into feaLib statements
import fontTools.feaLib.ast as feaast
import fontFeatures

def glyphref(g):
  if len(g) == 1:
    return feaast.GlyphName(g[0])
  return feaast.GlyphClass([feaast.GlyphName(x) for x in g])

def suborpos(lookups):
    for l in lookups:
      for aLookup in l:
        if not aLookup: continue
        for r in aLookup.rules:
          if isinstance(r, fontFeatures.Substitution): return "sub"
          if isinstance(r, fontFeatures.Positioning): return "pos"
          if isinstance(r, fontFeatures.Attachment): return "pos"

def _complex(self):
  import warnings
  warnings.warn("Can't currently express multiple lookups per position in AFDKO")
  return feaast.Comment("# Unparsing failed")

def asFeaAST(self):
  if len(self.lookups) > 0 and any([x is not None for x in self.lookups]):
    # Fill in the blanks
    self.lookups = [ x or [None] for x in self.lookups ]
    if suborpos(self.lookups) == "sub":
      routine = feaast.ChainContextSubstStatement
    else:
      routine = feaast.ChainContextPosStatement
    # Check for >1 lookups per position
    if any([x and len(x) > 1 for x in self.lookups]):
      return _complex(self)
    return routine(
      [glyphref(x) for x in self.precontext],
      [glyphref(x) for x in self.input],
      [glyphref(x) for x in self.postcontext],
      [ l[0] for l in self.lookups]
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
