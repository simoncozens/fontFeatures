class IMatra:
    takesBlock = False

    @classmethod
    def validate(self, tokens, verbaddress):
        from fontFeatures.parserTools import ParseError

        if len(tokens) != 3:
            raise ParseError("Wrong number of arguments", token[0].address, self)
        return True

    @classmethod
    def store(self, parser, tokens, doFilter=None):
        import fontFeatures
        from fontFeatures.ftUtils import get_glyph_metrics

        matra = parser.expandGlyphOrClassName(tokens[0].token)
        matras = parser.expandGlyphOrClassName(tokens[1].token)
        bases = parser.expandGlyphOrClassName(tokens[2].token)
        # Organise matras into overhang widths
        matras2bases = {}
        matrasAndOverhangs = [
            (m, -get_glyph_metrics(parser.font, m)["rsb"]) for m in matras
        ]
        for b in bases:
            w = get_glyph_metrics(parser.font, b)["width"]
            bestMatra = min(matrasAndOverhangs, key=lambda s: abs(s[1] - w))
            if not bestMatra in matras2bases:
                matras2bases[bestMatra] = []
            matras2bases[bestMatra].append(b)
        rv = []
        for k, v in matras2bases.items():
            rv.append(
                fontFeatures.Substitution(
                    [matra], postcontext=[v], replacement=[[k[0]]]
                )
            )
        return rv
