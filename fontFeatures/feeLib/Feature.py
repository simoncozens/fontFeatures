
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
    featurename = token.token
    if not featurename in parser.fea.features:
      parser.fea.features[featurename] = []
    for el in parser.parseString(block):
      # Check if it needs putting into a routine???
      parser.fea.features[featurename].append(el)
    return []
