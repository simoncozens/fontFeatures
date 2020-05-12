class SetWidth:
    takesBlock = False

    @classmethod
    def validate(self, tokens, verbaddress):
        from fontFeatures.parserTools import ParseError
        import re

        if len(tokens) > 2:
            raise ParseError("Too many arguments", verbaddress, self)
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
