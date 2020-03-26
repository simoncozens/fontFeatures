class Substitute:
  takesBlock = False

  @classmethod
  def validate(self, tokens, verbaddress):
    if not any(map(lambda x: x == "->", [t.token for t in tokens])):
      raise ParseError("No substitution operator (->) found", verbaddress, self)

    return True

  @classmethod
  def store(self, parser, tokens):
    import fontFeatures, re
    tokens = [t.token for t in tokens]
    op = tokens.index("->")
    inputs = tokens[0:op]
    for ix, i in enumerate(inputs):
      inputs[ix] = parser.expandGlyphOrClassName(i)
    outputs = tokens[op+1:]
    for ix, o in enumerate(outputs):
      m = re.match("^\$(\d+)(?:([\.~])(.*))?$", o)
      if m:
        outputs[ix] = list(inputs[int(m[1])-1])
        if m[2] == ".":
          for jx,g in enumerate(outputs[ix]):
            outputs[ix][jx] = g + "." + m[3]
        else:
          raise NotImplementedError
      else:
        outputs[ix] = parser.expandGlyphOrClassName(o)
    return [fontFeatures.Substitution(inputs, outputs)]
