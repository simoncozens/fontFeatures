
class Feature:
  takesBlock = True

  @classmethod
  def validateBlock(self, token, block, verbaddress):
    import re
    from fontFeatures.parserTools import ParseError
    if not re.match("^[a-z0-9]{4}$", token.token):
      raise ParseError("Invalid feature name", tokens.address, self)
    return True

  @classmethod
  def storeBlock(self, parser, token, block):
    if not token.token in parser.fea.features:
      parser.fea.features[token.token] = []
    contents = parser.parseString(block)
    print(token.token, block, contents)
    return []
