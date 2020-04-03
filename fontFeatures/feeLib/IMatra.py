class IMatra:
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
    matra = parser.expandGlyphOrClassName(tokens[0].token)
    matras = parser.expandGlyphOrClassName(tokens[1].token)
    bases = parser.expandGlyphOrClassName(tokens[2].token)
    # Organise matras into overhang widths
    matras2bases = {}
    matrasAndOverhangs = [ (m, -parser.get_glyph_metrics(m)["rsb"]) for m in matras]
    for b in bases:
    	w = parser.get_glyph_metrics(b)["width"]
    	bestMatra = min(matrasAndOverhangs, key = lambda s:abs(s[1]-w))
    	if not bestMatra in matras2bases:
    		matras2bases[bestMatra] = []
    	matras2bases[bestMatra].append(b)
    rv = []
    for k,v in matras2bases.items():
    	rv.append(fontFeatures.Substitution(
    		[matra],
    		postcontext=[v],
    		replacement = [[k[0]]]
  		))
    return rv
