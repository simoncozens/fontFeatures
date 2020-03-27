class InitMediFina:
  takesBlock = False

  @classmethod
  def validate(self, tokens, verbaddress):
    from fontFeatures.parserTools import ParseError
    if len(tokens) > 0:
      raise ParseError("Too many arguments", verbaddress, self)
    return True

  @classmethod
  def store(self, parser, tokens):
    from fontFeatures.parserTools import ParseError
    for c in ["inits", "medis", "finas"]:
      if not c in parser.fea.namedClasses:
        raise ParseError("Expected class %s not defined" % c, (), self)
    return parser.parseString("""
      Feature init { Substitute @inits~init -> @inits; };
      Feature medi { Substitute @medis~medi -> @medis; };
      Feature fina { Substitute @finas~fina -> @finas; };
    """)


