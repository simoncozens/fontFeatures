from fontTools.ttLib import TTFont
import fontTools.feaLib.ast as feaast

def glyphref(g):
  if len(g) == 1:
    return feaast.GlyphName(g[0])
  return feaast.GlyphClass([feaast.GlyphName(x) for x in g])

class FontFeatures:
  def __init__(self):
    self.namedClasses = {}
    self.routines = []
    self.features = {}

  def asFea(self):
    ff = feaast.FeatureFile()

    for k,v in self.namedClasses.items():
      asclass = feaast.GlyphClass([feaast.GlyphName(x) for x in v])
      ff.statements.append(feaast.GlyphClassDefinition(k, asclass))

    ff.statements.append(feaast.Comment(""))

    for k,v in self.routines:
      pass

    for k,v in self.features.items():
      f = feaast.FeatureBlock(k)
      for n in v:
        f.statements.append(n.asFea())
      ff.statements.append(f)
    return ff.asFea()

class Routine:
  def __init__(self, name, rules = [], address = None):
    self.name  = name
    self.rules = rules
    self.address = address

class Substitution:

  def __init__(self, input_, replacement, precontext = [], postcontext = [], address = None):
    self.precontext = precontext
    self.postcontext = postcontext
    self.input = input_
    self.replacement = replacement
    self.address = address

  def asFea(self):
    if len(self.input) == 1 and len(self.replacement) == 1:
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
    if len(self.input) == 1 and len(self.replacement) > 1:
      return feaast.MultipleSubstStatement(
        [glyphref(x) for x in self.precontext],
        glyphref(self.input[0]),
        [glyphref(x) for x in self.postcontext],
        [glyphref(x) for x in self.replacement],
        False
      )

    raise ValueError()
