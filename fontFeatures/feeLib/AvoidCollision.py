class AvoidCollision:
    takesBlock = False

    @classmethod
    def validate(self, tokens, verbaddress):
        from fontFeatures.parserTools import ParseError

        if tokens[-2].token != "kern" and tokens[-2].token != "raise":
            raise ParseError(
                "Mitigation strategy should be 'kern' or 'raise'",
                token[-2].address,
                self,
            )
        try:
            int(tokens[-1].token)
        except Exception as e:
            raise ParseError("Kern value should be integer", token[-1].address, self)
        return True

    @classmethod
    def store(self, parser, tokens, doFilter=None):
        import fontFeatures
        from fontFeatures.jankyPOS import JankyPos
        import collidoscope
        import warnings
        import beziers
        import itertools

        combinations = [parser.expandGlyphOrClassName(x.token) for x in tokens[0:-2]]
        mitigation = tokens[-2].token
        units = int(tokens[-1].token)
        janky = fontFeatures.jankyPOS.JankyPos(parser.font)
        col = collidoscope.Collidoscope(
            None, {"cursive": False, "faraway": True, "area": 0}, ttFont=parser.font
        )
        rv = []
        for element in itertools.product(*combinations):
            buf = janky.positioning_buffer(element)
            buf = janky.process_fontfeatures(buf, parser.fea)
            glyphs = []
            cursor = 0
            for g, vr in buf:
                offset = beziers.point.Point(
                    cursor + (vr.xPlacement or 0), vr.yPlacement or 0
                )
                glyphs.append(col.get_positioned_glyph(g, offset))
                glyphs[-1]["advance"] = vr.xAdvance
                cursor = cursor + vr.xAdvance
            overlaps = col.has_collisions(glyphs)
            if overlaps:
                warnings.warn(
                    "Overlap found in glyph sequence %s - mitigating"
                    % (" ".join(element))
                )
                intersects = [p1.intersection(p2) for p1, p2 in overlaps]
                assert len(intersects) == 1
                # If it's not, we have to find the leftmost intersection
                if mitigation == "kern":
                    correction = intersects[0][0].bounds().width + units
                    v = fontFeatures.ValueRecord(xAdvance=int(correction))
                    s = fontFeatures.Positioning(
                        [[element[0]], [element[1]]], [v, fontFeatures.ValueRecord()]
                    )
                else:
                    correction = intersects[0][0].bounds().height + units
                    v = fontFeatures.ValueRecord(yPlacement=int(correction))
                    s = fontFeatures.Positioning(
                        [[element[2]]], [v], postcontext=[[element[1]], [element[0]]]
                    )
                rv.append(s)
        return rv
