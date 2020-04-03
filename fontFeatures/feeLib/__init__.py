import importlib, inspect
from .. import FontFeatures
from ..parserTools import ParseContext
import re
import warnings

def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
        return '# [warning] %s\n' % ( message)

warnings.formatwarning = warning_on_one_line

class FeeParser:
  DEFAULT_PLUGINS = [
    "ClassDefinition",
    "Feature",
    "Substitute",
    "LoadPlugin",
    "Anchors"
  ]

  def __init__(self, font):
    self.font = font
    self.fea = FontFeatures()
    self.glyphs = font.getGlyphOrder()

    self.plugins = []
    self.verbs = {}

    for plugin in self.DEFAULT_PLUGINS:
      self.loadPlugin(plugin)

  def loadPlugin(self, plugin):
    mod = importlib.import_module(__name__+"."+plugin)
    classes = inspect.getmembers(mod, inspect.isclass)
    for verb, c in classes:
      self.verbs[verb] = c

  def parseFile(self, filename):
    with open(filename, 'r') as f:
      data = f.read()
    return self.parseString(data)

  def parseString(self, s):
    pc = ParseContext(s)
    pc.skipWhitespaceAndComments()
    returns = []
    while pc.moreToParse:
      verbaddress = pc.address
      verb = pc.expect(self.verbs.keys())
      pc.skipWhitespaceAndComments()
      if self.verbs[verb].takesBlock:
        token = pc.consumeToken()
        pc.skipWhitespaceAndComments()
        block = pc.returnBlock()
        self.verbs[verb].validateBlock(token, block, verbaddress)
        returns.extend(self.verbs[verb].storeBlock(self, token, block))
      else:
        tokens = pc.consumeTokens()
        self.verbs[verb].validate(tokens, verbaddress)
        returns.extend(self.verbs[verb].store(self, tokens))
      pc.skipWhitespaceAndComments()
    return returns

  def expandGlyphOrClassName(self, s):
    """Returns a list of glyphs expanded from a name. e.g.
        space    -> space
        @foo     -> contents of class foo
        @foo.sc  -> contents of class foo, suffixed by .sc
        @foo~sc  -> contents of class foo, with .sc removed
    """
    if not s.startswith("@"):
      m = re.match("(.*)([\.~])(.*)$", s)
      if not s in self.glyphs:
        warnings.warn("Couldn't find glyph '%s' in font" % s)
      return [ s ]
    s = s[1:]
    if s in self.fea.namedClasses: return self.fea.namedClasses[s]
    m = re.match("(.*)([\.~])(.*)$", s)
    if m:
      origclass = m[1]
      operation = m[2]
      suffix = m[3]
      if not origclass in self.fea.namedClasses:
        raise ValueError("Tried to expand glyph class '@%s' but @%s was not defined" % (s,origclass))
      origglyphs = self.fea.namedClasses[origclass]
      expanded = []
      for g in origglyphs:
        if operation == ".":
          newglyph = g+"."+suffix
        else:
          newglyph = g
          if newglyph.endswith("."+suffix): newglyph = newglyph[:-(len(suffix)+1)]
        if not newglyph in self.glyphs:
          op = operation == "." and "" or "de-"
          warnings.warn("# Couldn't find glyph '%s' in font during %ssuffixing operation @%s" % (newglyph,op, s))
        expanded.append(newglyph)
      return expanded

  def parse_languages(self, token):
    assert(token[0] == "<")
    assert(token[-1] == ">")
    token = token[1:-1]
    scriptlangs = token.split(",")
    return [ tuple(l.split("/")) for l in scriptlangs ]

  def categorize_glyph(self, glyphname):
    classdefs = self.font["GDEF"].table.GlyphClassDef.classDefs
    assert(glyphname in classdefs)
    if classdefs[glyphname] == 1: return ("base",None)
    if classdefs[glyphname] == 2: return ("ligature",None)
    if classdefs[glyphname] == 3:
        # Now find attachment class
        if self.font["GDEF"].table.MarkAttachClassDef:
          markAttachClassDef = self.font["GDEF"].table.MarkAttachClassDef.classDefs
          mclass = markAttachClassDef[glyphname]
        else:
          mclass = None
        return ("mark",mclass)
    if classdefs[glyphname] == 4: return ("component",None)
    raise ValueError