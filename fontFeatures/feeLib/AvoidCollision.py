class AvoidCollision:
  takesBlock = False

  @classmethod
  def validate(self, tokens, verbaddress):
    from fontFeatures.parserTools import ParseError
    if len(tokens) != 4:
      raise ParseError("Wrong number of arguments", token[0].address, self)
    if tokens[2].token != "kern":
      raise ParseError("Mitigation strategy should be 'kern'", token[2].address, self)
    try:
      int(tokens[3].token)
    except Exception as e:
      raise ParseError("Kern value should be integer", token[2].address, self)
    return True

  @classmethod
  def store(self, parser, tokens, doFilter = None):
    import fontFeatures
    import collidoscope
    import warnings
    import beziers
    class1 = parser.expandGlyphOrClassName(tokens[0].token)
    class2 = parser.expandGlyphOrClassName(tokens[1].token)
    mitigation = tokens[2].token
    units = int(tokens[3].token)
    col = collidoscope.Collidoscope(None,{"cursive": False }, ttFont=parser.font)
    rv = []
    for left in class1:
      for right in class2:
        # XXX This should use namvezvez positioning
        lglyph = col.get_positioned_glyph(left, beziers.point.Point(0,0))
        width = parser.get_glyph_metrics(left)["width"]
        rglyph = col.get_positioned_glyph(right, beziers.point.Point(width,0))
        overlaps = col.find_overlapping_paths(lglyph, rglyph)
        if overlaps:
          warnings.warn("Overlap found in glyph pair /%s/%s - mitigating" % (left,right))
          intersects = [ p1.intersection(p2) for p1,p2 in overlaps ]
          assert(len(intersects) == 1)
          # If it's not, we have to find the leftmost intersection
          correction = intersects[0][0].bounds().width + units
          v = fontFeatures.ValueRecord(xAdvance=int(correction))
          s = fontFeatures.Positioning([left,right], [v,fontFeatures.ValueRecord()])
          rv.append(s)
    return rv
