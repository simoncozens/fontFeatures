
class Anchors:
  takesBlock = True

  @classmethod
  def validateBlock(self, token, block, verbaddress):
    from ..parserTools import ParseContext
    from fontFeatures.parserTools import ParseError
    import re
    b = ParseContext(block)
    names = []
    while b.moreToParse:
      name = b.consumeToken().token
      if name in names:
        raise ParseError("Repeated anchor %s" % name, token.address, self)
      names.append(name)
      x = b.consumeToken()
      if not re.match("^<-?[\\d.]+$", x.token):
        raise ParseError("Invalid X coordinate for %s anchor" % name, token.address, self)
      y = b.consumeToken()
      if not re.match("^-?[\\d.]+>$", y.token):
        raise ParseError("Invalid Y coordinate for %s anchor" % name, token.address, self)
    return True

  @classmethod
  def storeBlock(self, parser, token, block):
    from ..parserTools import ParseContext
    glyphs = parser.expandGlyphOrClassName(token.token)
    anchors = {}
    b = ParseContext(block)
    while b.moreToParse:
      name = b.consumeToken().token
      x = b.consumeToken().token
      y = b.consumeToken().token
      anchors[name] = ( int(x[1:]), int(y[:-1]) ) # Or float?

    for g in glyphs:
      if not g in parser.fea.anchors:
        parser.fea.anchors[g] = {}
      parser.fea.anchors[g].update(anchors)

    return []


class Attach:
  takesBlock = False

  @classmethod
  def validate(self, tokens, verbaddress):
    from fontFeatures.parserTools import ParseError
    if len(tokens) != 2: 
      raise ParseError("Wrong number of arguments", token[0].address, self)
    if not (tokens[0].token.startswith("&")):
      raise ParseError("Anchor class should start with &", token[0].address, self)
    if not (tokens[1].token.startswith("&")):
      raise ParseError("Anchor class should start with &", token[0].address, self)

    return True

  @classmethod
  def store(self, parser, tokens):
    import fontFeatures
    aFrom = tokens[0].token[1:]
    aTo = tokens[1].token[1:]
    bases = [] # These may actually be marks in a mkmk case, but we'll sort that
    marks = []
    for k,v in parser.fea.anchors.items():
      if aFrom in v: bases.append( (k, v[aFrom]) )
      if aTo in v:   marks.append( (k, v[aTo]) )
    return [ fontFeatures.Attachment(aFrom, aTo, bases, marks) ]
