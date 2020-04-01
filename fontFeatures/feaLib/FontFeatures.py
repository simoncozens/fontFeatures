# Code for converting a FontFeatures object into feaLib statements
import fontTools.feaLib.ast as feaast

def addLanguageSystemStatements(self, ff):
  self.hoistLanguages()
  if len(self.languages) == 0: return
  if len(self.languages) == 1 and self.languages[0] == ("DLFT", "dflt"): return
  # Sort into scripts and languages, resolve wildcards
  for l in self.languages:
    ff.statements.append(feaast.LanguageSystemStatement(*l))

def asFea(self):
  return self.asFeaAST().asFea()

def asFeaAST(self):
  """Returns this font's features as a feaLib AST object, for later
  translation to AFDKO code."""
  from fontFeatures import Routine
  ff = feaast.FeatureFile()

  addLanguageSystemStatements(self, ff)
  for k,v in self.namedClasses.items():
    asclass = feaast.GlyphClass([feaast.GlyphName(x) for x in v])
    ff.statements.append(feaast.GlyphClassDefinition(k, asclass))

  ff.statements.append(feaast.Comment(""))

  for k in self.routines:
    assert(isinstance(k, Routine))
    if not k.inlined:
      ff.statements.append(k.asFeaAST())

  for k,v in self.features.items():
    f = feaast.FeatureBlock(k)
    for n in v:
      # If it's a routine and it's in self.routines, use a reference
      if isinstance(n, Routine) and n in self.routines:
        f.statements.append(feaast.LookupReferenceStatement(n.asFeaAST()))
      else:
        f.statements.append(n.asFeaAST())
    ff.statements.append(f)
  return ff
