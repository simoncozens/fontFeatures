# Useful routines to get what we need from fontTools

def categorize_glyph(font, glyphname):
  classdefs = font["GDEF"].table.GlyphClassDef.classDefs
  assert(glyphname in classdefs)
  if classdefs[glyphname] == 1: return ("base",None)
  if classdefs[glyphname] == 2: return ("ligature",None)
  if classdefs[glyphname] == 3:
      # Now find attachment class
      if font["GDEF"].table.MarkAttachClassDef:
        markAttachClassDef = font["GDEF"].table.MarkAttachClassDef.classDefs
        mclass = markAttachClassDef[glyphname]
      else:
        mclass = None
      return ("mark",mclass)
  if classdefs[glyphname] == 4: return ("component",None)
  raise ValueError

def get_glyph_metrics(font, glyphname):
  metrics = {
    "width":   font["hmtx"][glyphname][0],
    "lsb":     font["hmtx"][glyphname][1],
  }
  if "glyf" in font:
    glyf = font["glyf"][glyphname]
    metrics["xMin"], metrics["xMax"], metrics["yMin"], metrics["yMax"] = glyf.xMin, glyf.xMax, glyf.yMin, glyf.yMax
  else:
    bounds = font.getGlyphSet()[glyphname]._glyph.calcBounds(font.getGlyphSet())
    metrics["xMin"], metrics["yMin"], metrics["xMax"], metrics["yMax"] = bounds
  metrics["rsb"] = metrics["width"] - metrics["xMax"]
  return metrics