
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

class FeatureName:
  takesBlock = False

  @classmethod
  def validate(self, tokens, verbaddress):
    from fontFeatures.parserTools import ParseError
    if not (tokens[0].token.startswith("\"") or tokens[0].token.startswith("'")):
      raise ParseError("Feature name should be a string", token[0].address, self)
    if not (tokens[-1].token.endswith("\"") or tokens[-1].token.endswith("'")):
      raise ParseError("Feature name should be a string", token[-1].address, self)
    return True

  @classmethod
  def store(self, parser, tokens):
    import warnings
    warnings.warn("Feature naming not currently implemented")
    return []
