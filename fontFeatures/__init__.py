from fontTools.ttLib import TTFont

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

  def addRoutine(self, r):
    assert(isinstance(r,Routine))
    self.routines.append(r)

  from .feaLib.FontFeatures import asFea, asFeaAST

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

  from .feaLib.Routine import asFea, asFeaAST

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

  from .feaLib.Substitution import asFea, asFeaAST