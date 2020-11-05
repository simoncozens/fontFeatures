# XXX This currently will not work. It requires porting to the new system.

class KernToDistance:
    takesBlock = False

    @classmethod
    def validate(self, tokens, verbaddress):
        from fontFeatures.parserTools import ParseError

        if len(tokens) < 3:
            raise ParseError("Too few arguments", verbaddress, self)

        try:
            int(tokens[-1].token)
        except Exception as e:
            raise ParseError(
                "Distance value should be positive integer", token[-1].address, self
            )

        return True

    @classmethod
    def store(self, parser, tokens):
        from glyphtools import determine_kern, bin_glyphs_by_metric
        import fontFeatures
        import itertools

        units = int(tokens[-1].token)
        kerns = []

        bincount = 5
        lefts = parser.expandGlyphOrClassName(tokens[0].token)
        rights = parser.expandGlyphOrClassName(tokens[1].token)

        def make_kerns(rise=0, context=[], direction="LTR"):
            kerns = []
            for l in lefts:
                for r in rights:
                    if direction == "LTR":
                        kern = determine_kern(parser.font, l, r, units, offset1=(0, rise))
                    else:
                        kern = determine_kern(parser.font, r, l, units, offset1=(0, rise))
                    if abs(kern) < 5:
                        continue
                    v = fontFeatures.ValueRecord(xAdvance=kern)
                    kerns.append(
                        fontFeatures.Positioning(
                            [[r]], [v], precontext=[[l]], postcontext=context
                        )
                    )
            return kerns

        context = [parser.expandGlyphOrClassName(x.token) for x in tokens[2:-1]]
        if len(context) == 0:
            return [fontFeatures.Routine(rules=make_kerns())]

        kerns = []
        binned_contexts = [
            bin_glyphs_by_metric(parser.font, glyphs, "rise", bincount=bincount)
            for glyphs in context
        ]
        for c in itertools.product(*binned_contexts):
            totalrise = sum([x[1] for x in c])
            precontext = [x[0] for x in c]
            kerns.extend(make_kerns(totalrise, context=precontext, direction="RTL"))

        return [fontFeatures.Routine(rules=kerns)]
