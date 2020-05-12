from fontTools.ttLib import TTFont
from collections import OrderedDict
from fontTools.feaLib.ast import ValueRecord
from itertools import chain

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
    self.features = OrderedDict()
    self.anchors = {}
    self.scratch = {} # Space for items to communicate context to each other. :(
    self.doneUsageMarking = False

  def addRoutine(self, r):
    assert(isinstance(r,Routine))
    self.routines.append(r)
    r.parent = self

  def addFeature(self, name, rs):
    if not name in self.features: self.features[name] = []
    for r in rs:
      r.parent = self
      self.features[name].append(r)

  def allRoutines(self):
    routines = set(self.routines)
    for k,v in self.features.items():
      for n in v:
        if isinstance(n, Routine):
          routines.add(n)
    return list(routines)

  def allRules(self, ruletype=None):
    rules = [ ]
    for r in self.allRoutines():
      rules.extend(r.rules)
    for k,v in self.features.items():
      for n in v:
        if not isinstance(n, Routine):
          rules.extend(n.rules)

    if ruletype:
      rules = filter(lambda x: isinstance(x, ruletype), rules)
    return rules

  def markRoutineUseInChains(self):
    if self.doneUsageMarking: return
    for r in self.allRoutines():
      r.usedin = set()
    for chain in self.allRules(Chaining):
      for routinelist in chain.lookups:
        if not routinelist: continue
        for routine in routinelist:
          # Using a set here so it is safe to call more than once
          routine.usedin.add(chain)
    self.doneUsageMarking = True

  from .feaLib.FontFeatures import asFea, asFeaAST

  def hoist_languages(self):
    # Sort into scripts and languages, resolve wildcards
    scripts = OrderedDict()
    count = 0
    def add_language(p):
      nonlocal scripts
      nonlocal count
      s,l = p
      if not s in scripts: scripts[s] = []
      if l == "*": return
      if not l in scripts[s]:
        count = count + 1
        scripts[s].append(l)

    for k in self.routines:
      if k.languages:
        for l in k.languages: add_language(l)
    for feat in self.features.values():
      for thing in feat:
        if hasattr(thing, "languages") and thing.languages:
          for l in thing.languages: add_language(l)

    if count > 0 and not "DFLT" in scripts:
      scripts["DFLT"] = []
      scripts.move_to_end("DFLT", last=False)
    if count > 0 and not "dflt" in scripts["DFLT"]:
      scripts["DFLT"].insert(0, "dflt")

    self.scripts_and_languages = scripts

class Routine:
  def __init__(self, name = "", rules = None, address = None, inlined = False, languages = None, parent = None, flags = 0):
    self.name  = name
    if rules:
      self.rules = rules
    else:
      self.rules = []
    self.address = address
    self.comments = []
    self.inlined = inlined
    self.languages = languages
    self.parent = parent
    self.flags = flags

  def addRule(self, rule):
    assert(isinstance(rule, Rule))
    self.rules.append(rule)

  def addComment(self, comment):
    self.comments.append(comment)

  @property
  def involved_glyphs(self):
    return set.union(*[r.involved_glyphs for r in self.rules])

  from .feaLib.Routine import asFea, asFeaAST, feaPreamble

class Rule:
  def asFea(self):
    return self.asFeaAST().asFea()
  def feaPreamble(self, ff):
    return []

class Substitution(Rule):
  """A substitution represents any kind of exchange of one set of glyphs for
  another: single substitutions, multiple substitutions and ligatures are all
  substitutions. Optionally, substitutions may be followed by precontext and
  postcontext."""

  def __init__(self, input_, replacement,
               precontext = [], postcontext = [],
               address = None, languages = None,
               lookups = [], flags = 0):
    self.precontext = precontext
    self.postcontext = postcontext
    self.input = input_
    self.replacement = replacement
    self.address = address
    self.lookups = lookups
    self.languages = languages
    self.flags = flags

  @property
  def involved_glyphs(self):
    i = set(chain.from_iterable(self.input))
    o = set(chain.from_iterable(self.replacement))
    b = set(chain.from_iterable(self.precontext))
    a = set(chain.from_iterable(self.postcontext))
    return i | o | b | a

  from .feaLib.Substitution import asFeaAST

class Chaining(Rule):
  # For now
  def __init__(self, input_,
               precontext = [], postcontext = [],
               address = None, languages = None,
               lookups = [], flags = 0):
    self.precontext = precontext
    self.postcontext = postcontext
    self.input = input_
    self.address = address
    self.lookups = lookups
    self.languages = languages
    self.flags = flags

  from .feaLib.Chaining import asFeaAST, feaPreamble

  @property
  def involved_glyphs(self):
    i = set(chain.from_iterable(self.input))
    b = set(chain.from_iterable(self.precontext))
    a = set(chain.from_iterable(self.postcontext))
    return i | b | a

class Positioning(Rule):
  def __init__(self, glyphs, valuerecords,
             precontext = [], postcontext = [],
             address = None, languages = None,
             lookups = [], flags = 0):
    self.precontext = precontext
    self.postcontext = postcontext
    assert(len(glyphs) == len(valuerecords))
    self.glyphs = glyphs
    self.valuerecords = valuerecords
    self.address = address
    self.lookups = lookups
    self.languages = languages
    self.flags = flags

  @property
  def involved_glyphs(self):
    i = set(chain.from_iterable(self.glyphs))
    b = set(chain.from_iterable(self.precontext))
    a = set(chain.from_iterable(self.postcontext))
    return i | b | a

  from .feaLib.Positioning import asFeaAST

class Attachment(Rule):
  def __init__(self, base_name, mark_name, bases = None, marks = None, flags = 0, address = None):
    self.base_name = base_name
    self.mark_name = mark_name
    self.bases = bases or {}
    self.marks = marks or {}
    self.flags = flags
    self.address = address

  @property
  def is_cursive(self):
    return self.base_name == "cursive_entry" # XXX

  from .feaLib.Attachment import asFeaAST, feaPreamble
  @property
  def involved_glyphs(self):
    b = set(self.bases.keys())
    m = set(self.marks.keys())
    return b | m

