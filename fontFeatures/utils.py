# Port of glyphtools.categorize_glyph, isolated here to reduce
# dependencies.


def categorize_glyph(font, glyphname):
    """Return the category of the given glyph.

    Args:
        font: a ``fontTools`` TTFont object OR a ``glyphsLib`` GSFontMaster
            object OR a ``babelfont`` Font object.
        glyphname: name of the glyph.

    Returns:
        A two-element tuple. The first element is one of the following
        strings: ``unknown``, ``base``, ``mark``, ``ligature``, ``component``.
        If the glyph is a mark, the second element is the mark attachment
        class number.
    """
    if hasattr(font, "userData"):  # Glyphs
        c = font.font.glyphs[glyphname].category
        sc = font.font.glyphs[glyphname].subCategory
        if sc == "Ligature":
            return ("ligature", None)
        if c == "Mark":
            return ("mark", None)
        return ("base", None)
    if hasattr(font, "_set_kerning"):  # Babelfont 1/2/3
        if hasattr(font, "_master_map") or hasattr(font, "get_glyph_layer"):
            return (font.glyphs[glyphname].category, None)  # Babelfont 3
        else:
            return (font[glyphname].category, None)  # Babelfont 1/2

    # TT font
    if "GDEF" not in font:
        return ("unknown", None)
    gdef = font["GDEF"].table
    classdefs = gdef.GlyphClassDef.classDefs
    if glyphname not in classdefs:
        return ("unknown", None)
    if classdefs[glyphname] == 1:
        return ("base", None)
    if classdefs[glyphname] == 2:
        return ("ligature", None)
    if classdefs[glyphname] == 3:
        # Now find attachment class
        mclass = None
        if gdef.MarkAttachClassDef:
            classdef = gdef.MarkAttachClassDef.classDefs
            if glyphname in classdef:
                mclass = classdef[glyphname]
        return ("mark", mclass)
    if classdefs[glyphname] == 4:
        return ("component", None)
    return ("unknown", None)
