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
    texttokens = [t.token for t in tokens]
    op = texttokens.index("->")
    inputs = []
    addingToClass = False
    for ix, i in enumerate(texttokens[0:op]):
      if i[0] == "[":
        inputs.append(parser.expandGlyphOrClassName(i[1:]))
        addingToClass = True
      elif addingToClass:
        if i[-1] == "]":
          addingToClass = False
          i = i[:-1]
        inputs[-1].extend(parser.expandGlyphOrClassName(i))
      else:
        inputs.append(parser.expandGlyphOrClassName(i))
    outputs = texttokens[op+1:]
    languages = None
    if outputs[-1].startswith("<"):
      languages = parser.parse_languages(outputs[-1])
      outputs = outputs[:-1]
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
    return [fontFeatures.Substitution(inputs, outputs, languages = languages)]
