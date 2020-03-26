class Substitute:
  takesBlock = False

  @classmethod
  def validate(self, tokens, verbaddress):
    if not any(map(lambda x: x == "->", [t.token for t in tokens])):
      raise ParseError("No substitution operator (->) found", verbaddress, self)

    return True

  @classmethod
  def store(self, parser, tokens):
    import fontFeatures
    return [fontFeatures.Substitution([], [])]
