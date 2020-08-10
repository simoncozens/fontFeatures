from fontFeatures.feeLib import FeePlugin


class SetWidth(FeePlugin):
    takesBlock = False
    arguments = 2

    @classmethod
    def validate(self, tokens, verbaddress):
        from fontFeatures.parserTools import ParseError
        import re
        self.validate_tokencount(tokens, verbaddress)
        if not re.match("^\d+%?", tokens[1].token):
            raise ParseError(
                "Width argument should be integer units or percentage",
                tokens[1].address,
                self,
            )
        return True

    @classmethod
    def store(self, parser, tokens, doFilter=None):
        from babelfont.otf.font import OTFont

        glyphs = parser.expandGlyphOrClassName(tokens[0].token)
        width = tokens[1].token
        if width.endswith("%"):
            wtype = "relative"
            width = int(width[:-1]) / 100
        else:
            wtype = "absolute"
            width = int(width)
        for g in glyphs:
            f = OTFont(parser.font)
            glyph = f.layers[0][g]
            if wtype == "relative":
                glyph.width = glyph.width * width
            else:
                glyph.width = width
        return []

class DuplicateGlyphs(FeePlugin):
    takesBlock = False
    arguments = 2

    @classmethod
    def validate(self, tokens, verbaddress):
        from fontFeatures.parserTools import ParseError
        self.validate_tokencount(tokens, verbaddress)

    @classmethod
    def store(self, parser, tokens):
        oldglyphs = parser.expandGlyphOrClassName(tokens[0].token)
        newglyphs = parser.expandGlyphOrClassName(tokens[1].token, mustExist = False)
        if len(oldglyphs) != len(newglyphs):
            raise ParseError(
                "Length of new glyphs should be the same as old glyphs",
                tokens[1].address,
                self,
            )
        import glyphtools
        import warnings
        for o,n in zip(oldglyphs, newglyphs):
            if n in parser.glyphs:
                warnings.warn("Glyph '%s' already exists" % n)
                continue
            glyphtools.duplicate_glyph(parser.font, o, n)
            if "GDEF" in parser.font:
                oldcat, maclass = glyphtools.categorize_glyph(parser.font, o)
                glyphtools.set_glyph_category(parser.font, n, oldcat, maclass)
            parser.fontModified = True
        parser.glyphs = parser.font.getGlyphOrder()
        return []
