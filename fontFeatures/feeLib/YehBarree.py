class YBFixOverhang:
  takesBlock = False

  @classmethod
  def validate(self, tokens, verbaddress):
    from fontFeatures.parserTools import ParseError
    if len(tokens) != 3:
      raise ParseError("Wrong number of arguments", token[0].address, self)
    return True

  @classmethod
  def store(self, parser, tokens, doFilter = None):
    import fontFeatures
    from fontFeatures.ftUtils import get_glyph_metrics, bin_glyphs_by_metric
    import warnings
    yehbarrees = parser.expandGlyphOrClassName(tokens[0].token)
    medis = parser.expandGlyphOrClassName(tokens[1].token)
    inits = parser.expandGlyphOrClassName(tokens[2].token)
    binned_medis = bin_glyphs_by_metric(parser.font, medis, "width", bincount = 4)
    binned_inits = bin_glyphs_by_metric(parser.font, inits, "width", bincount = 4)
    rules = []
    maxchainlength = 0
    for yb in yehbarrees:
      overhang =  -get_glyph_metrics(parser.font,yb)["rsb"]
      workqueue = [[x] for x in binned_inits]
      while workqueue:
        string = workqueue.pop(0)
        totalwidth = sum([x[1] for x in string])
        if totalwidth > overhang: continue
        maxchainlength = max(maxchainlength, len(string))
        adjustment = overhang - totalwidth + 20
        postcontext = [ x[0] for x in string[:-1] ] + [ [yb] ]
        input_ = string[-1]
        # example = [x[0] for x in postcontext] + [input_[0][0]]
        # warnings.warn("Yeh Barree collision found in e.g. %s - adding %i units" % (" ".join(example), adjustment))

        rules.append(
          fontFeatures.Positioning(
            [input_[0]],
            [fontFeatures.ValueRecord(xAdvance=adjustment)],
            postcontext = postcontext
            )
        )
        for medi in binned_medis:
          workqueue.append([medi] + string)
    warnings.warn("Yeh Barree collision maximum chain length was %i glyphs" % maxchainlength)
    return [fontFeatures.Routine(rules=rules)]

class YBDropDots:
  takesBlock = False

  @classmethod
  def validate(self, tokens, verbaddress):
    from fontFeatures.parserTools import ParseError
    if len(tokens) != 4:
      raise ParseError("Wrong number of arguments", tokens[0].address, self)
    return True

  @classmethod
  def store(self, parser, tokens, doFilter = None):
    import fontFeatures
    import itertools
    from fontFeatures.ftUtils import get_glyph_metrics, bin_glyphs_by_metric
    import warnings
    yehbarrees = parser.expandGlyphOrClassName(tokens[0].token)
    medis = parser.expandGlyphOrClassName(tokens[1].token)
    dots = parser.expandGlyphOrClassName(tokens[2].token)
    maxchainlength = int(tokens[3].token)
    binned_medis = bin_glyphs_by_metric(parser.font, medis, "rise", bincount = 10)
    rules = []
    for i in range(0,maxchainlength):
      for string in itertools.combinations_with_replacement(binned_medis, i):
        totalrise = sum([ x[1] for x in string])
        postcontext = [ x[0] for x in string ] + [ yehbarrees ]
        rules.append(
          fontFeatures.Positioning(
            [dots],
            [fontFeatures.ValueRecord(yPlacement=-(totalrise+300))],
            postcontext = postcontext
            )
        )
    return [fontFeatures.Routine(rules=rules,flags=0)]
