from fontTools.ttLib import TTFont
import fontTools.feaLib.ast as feaast

def glyphref(g):
  if len(g) == 1:
    return feaast.GlyphName(g[0])
  return feaast.GlyphClass([feaast.GlyphName(x) for x in g])

class FontFeatures:
  """The FontFeatures class is a way of representing the transformations -
  substitutions and positionings - going on inside a font at a semantically
  high level. It aims to be independent of and unconstrained by the OpenType
  representation, with the assumption that these high-level objects can be
  either "compiled down" into AFDKO feature code or directly written to the
  GSUB/GPOS tables of a font.

  FontFeatures aims to marshal data between OTF binary representations,
  AFDKO feature code, FontDame, and a new language called FEE (Font
  Engineering language with Extensibility).

  A FontFeatures representation of a font will make use of two other top-level
  concepts: Features and Routines. Routines are collections of rules; they play
  a similar function to the AFDKO concept of a lookup, but unlike lookups,
  Routines do not need to be comprised of rules of the same type. You can think
  of them as functions that are called on a glyph string."""
  def __init__(self):
    self.namedClasses = {}
    self.routines = []
    self.features = {}

  def asFea(self):
    return self.asFeaAST().asFea()

  def asFeaAST(self):
    """Returns this font's features as a feaLib AST object, for later
    translation to AFDKO code."""
    ff = feaast.FeatureFile()

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

    def addRoutine(self, r):
      assert(isinstance(r,Routine))
      self.routines.append(r)

class Routine:
  def __init__(self, name = None, rules = None, address = None, inlined = False, languages = None):
    self.name  = name
    if rules:
      self.rules = rules
    else:
      self.rules = []
    self.address = address
    self.comments = []
    self.inlined = inlined
    self.languages = languages

  def addRule(self, rule):
    assert(isinstance(rule, Substitution))
    self.rules.append(rule)

  def addComment(self, comment):
    self.comments.append(comment)

  def asFeaAST(self):
    if self.languages and len(self.languages) > 1:
      raise ValueError("Can't unparsed shared routine yet")
    # Arrange into rules of similar type
    if self.name:
      f = feaast.LookupBlock(name = self.name)
    else:
      f = feaast.Block()
    if self.languages and not (self.languages[0][0] == "DFLT" and self.languages[0][1] == "dflt"):
      f.statements.append(feaast.ScriptStatement(self.languages[0][0]))
      f.statements.append(feaast.LanguageStatement(self.languages[0][1]))
    for x in self.comments:
      f.statements.append(Comment(x))

    for x in self.rules:
      f.statements.append(x.asFeaAST())
    return f

  def asFea(self):
    return self.asFeaAST().asFea()


class Substitution:
  """A substitution represents any kind of exchange of one set of glyphs for
  another: single substitutions, multiple substitutions and ligatures are all
  substitutions. Optionally, substitutions may be followed by precontext and
  postcontext."""

  def __init__(self, input_, replacement,
               precontext = [], postcontext = [],
               address = None, languages = None,
               lookups = []):
    self.precontext = precontext
    self.postcontext = postcontext
    self.input = input_
    self.replacement = replacement
    self.address = address
    self.lookups = lookups
    self.languages = languages

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
