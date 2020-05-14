class YBSettings:
  takesBlock = False

  @classmethod
  def validate(self, tokens, verbaddress):
    from fontFeatures.parserTools import ParseError
    if len(tokens) != 2:
      raise ParseError("Wrong number of arguments", token[0].address, self)
    return True

  @classmethod
  def getSettings(self, parser):
    if "fee-yb-settings" not in parser.fea.scratch:
      parser.fea.scratch["fee-yb-settings"] = {
        "OverhangPadding": 20,
        "DropDotsBinCount": 8
      }
    return parser.fea.scratch["fee-yb-settings"]

  @classmethod
  def store(self, parser, tokens, doFilter = None):
    keyword = tokens[0].token
    value   = tokens[1].token
    self.getSettings(parser)
    parser.fea.scratch["fee-yb-settings"][keyword] = value
    return []

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
    settings = YBSettings.getSettings(parser)
    yehbarrees = parser.expandGlyphOrClassName(tokens[0].token)
    medis = parser.expandGlyphOrClassName(tokens[1].token)
    inits = parser.expandGlyphOrClassName(tokens[2].token)
    binned_medis = bin_glyphs_by_metric(parser.font, medis, "width", bincount = 4)
    binned_inits = bin_glyphs_by_metric(parser.font, inits, "width", bincount = 4)
    rules = []
    maxchainlength = 0
    longeststring = []
    for yb in yehbarrees:
      overhang =  -get_glyph_metrics(parser.font,yb)["rsb"]
      workqueue = [[x] for x in binned_inits]
      while workqueue:
        string = workqueue.pop(0)
        totalwidth = sum([x[1] for x in string])
        if totalwidth > overhang: continue

        adjustment = overhang - totalwidth + int(settings["OverhangPadding"])
        postcontext = [ x[0] for x in string[:-1] ] + [ [yb] ]
        input_ = string[-1]
        example = [input_[0][0]] + [x[0] for x in postcontext]
        maxchainlength = max(maxchainlength, len(string))

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
    settings["ComputedMaxChainLength"] = maxchainlength
    return [fontFeatures.Routine(rules=rules, flags=8)]

class YBDropDots:
  takesBlock = False

  @classmethod
  def validate(self, tokens, verbaddress):
    from fontFeatures.parserTools import ParseError
    if len(tokens) != 3:
      raise ParseError("Wrong number of arguments", tokens[0].address, self)
    return True

  @classmethod
  def store(self, parser, tokens, doFilter = None):
    import fontFeatures
    import itertools
    from fontFeatures.ftUtils import get_glyph_metrics, bin_glyphs_by_metric
    import warnings
    settings = YBSettings.getSettings(parser)
    if "DropDotsDepth" not in settings:
      raise ValueError("DropDotsDepth setting is required")
    if "MaxChainLength" not in settings:
      if "ComputedMaxChainLength" not in settings:
        raise ValueError("MaxChainLength setting is required")
      settings["MaxChainLength"] = settings["ComputedMaxChainLength"]

    yehbarrees = parser.expandGlyphOrClassName(tokens[0].token)
    medis = parser.expandGlyphOrClassName(tokens[1].token)
    dots = parser.expandGlyphOrClassName(tokens[2].token)
    # XXX check anchors
    binned_medis = bin_glyphs_by_metric(parser.font, medis, "rise", bincount = int(settings["DropDotsBinCount"]))
    rules = []
    for i in range(0,int(settings["MaxChainLength"])):
      #XXX This isn't creating all combinations
      for bases in itertools.combinations_with_replacement(binned_medis, i):
        for marks in itertools.combinations_with_replacement([dots,None], i):
          totalrise = sum([ x[1] for x in bases])
          justbases = [ x[0] for x in bases ]
          string = [val for pair in zip(justbases, marks) for val in pair]
          postcontext = [i for i in string if i] + [ yehbarrees ]
          rules.append(
            fontFeatures.Positioning(
              [dots],
              [fontFeatures.ValueRecord(yPlacement=-(totalrise+int(settings["DropDotsDepth"])))],
              postcontext = postcontext
              )
          )
    r = fontFeatures.Routine(rules=list(reversed(rules)),flags=0x10 )
    r.markFilteringSet=dots
    return [r]
