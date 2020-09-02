"""
Collision Detection
-------------------

Normally, in a font, you don't want glyphs to bang into each other. But sometimes
they do, and, especially when you're dealing with lots of layout rules and anchors
and cursive positioning, it can be difficult to isolate precisely which sequences
of glyphs cause collisions and why.

The ``IfCollides`` plugin helps to mitigate this problem by enumerating the
possibilities of a glyph sequence, looking for sets of glyphs which collide,
and then calling a routine on those glyph sequences::

        Routine LiftDamma { Position DAMMA <yPlacement=-100>; };
        IfCollides @medi_init @above_marks DAMMA @kafgaf -> LiftDamma;

The ``IfCollides`` verb takes a sequence of glyph selectors, an arrow (``->``),
and the name of a routine. If there are collisions in the expansion of the glyph
sequence, based on the rules in the FEE file up to this point, then a rule is
emitted which chains to the ``LiftDamma`` routine at *each glyph position*.
(This may not be what you want.)

If there are *lots* of collisions in the expansion (where 'lots' is defined as
>60%), then a chaining rule is emitted for the whole sequence, and you get
a warning telling you that this may not be what you want.
"""

import fontFeatures
from fontFeatures.jankyPOS import JankyPos
import collidoscope
import warnings
import beziers
import itertools
from functools import reduce

GRAMMAR = """
IfCollides_Args = (gsws)+:sequence '->' ws <letter+>:routine -> (sequence,routine)
gsws = glyphselector:g ws? -> g
"""

VERBS = ["IfCollides"]


class IfCollides:
    @classmethod
    def action(self, parser, sequence, routine):
        combinations = [g.resolve(parser.fontfeatures, parser.font) for g in sequence]
        named = [x for x in parser.fontfeatures.routines if x.name == routine]
        if len(named) != 1:
            raise ValueError("Could not find routine called %s" % routine)
        routine = named[0]
        janky = fontFeatures.jankyPOS.JankyPos(parser.font, direction="RTL")
        col = collidoscope.Collidoscope(
            None, {"cursive": False, "faraway": True, "area": 0.1}, ttFont=parser.font,
        )
        col.direction = "RTL"
        r = []
        clashes = 0
        total = reduce(lambda x, y: x * y, [len(x) for x in combinations], 1)
        warnings.warn("Enumerating %i sequences" % total)
        for element in itertools.product(*combinations):
            buf = janky.positioning_buffer(element)
            buf = janky.process_fontfeatures(buf, parser.fontfeatures)
            glyphs = []
            cursor = 0
            for info in buf:
                g, vr = info["glyph"], info["position"]
                offset = beziers.point.Point(
                    cursor + (vr.xPlacement or 0), vr.yPlacement or 0
                )
                glyphs.append(col.get_positioned_glyph(g, offset))
                glyphs[-1]["advance"] = vr.xAdvance
                cursor = cursor + vr.xAdvance
            overlaps = col.has_collisions(glyphs)
            if not overlaps:
                continue
            clashes = clashes + 1
            if clashes >= 0.6 * total:
                break
            # warnings.warn("Overlap found in glyph sequence %s" % (" ".join(element)))
            r.append(fontFeatures.Chaining(
                [ [x] for x in element ],
                lookups = [ [routine] for x in element ]
            ))
        if clashes >= 0.6 * total:
            warnings.warn("Most enumerations of sequence overlapped, calling routine on whole sequence instead. This may not be what you want!")
            r = [fontFeatures.Chaining(
                combinations,
                lookups = [ [routine] for x in combinations ]
            )]
        return [fontFeatures.Routine(rules=r)]
