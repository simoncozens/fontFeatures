"""
Matra selection
===============

In Devanagari fonts, it is common to have a basic glyph to represent the "i"
matra, and then a set of variant glyphs of differing widths. The "arm" of the
"i" matra should reach the stem of the following base consonant, which leads to an
interesting font engineering question: how do we produce a set of substitution
rules which replaces the basic glyph for each width-specific variant most
appropriate to the widths of the each consonant?

Obviously you don't want to work that out manually, because the next time you
engineer a Devanagari font you have to work it out again, and no programmer is
going to do the same set of operations more than once without automating it.

The ``IMatra`` plugin provides a verb which matches the consonants to the
matra variant with the appropriate sized arm and emits substitution rules. It
takes a glyph selector to represent the consonants, the basic i-matra glyph,
and a glyph selector for all the i-matra variants::

    LoadPlugin IMatra;
    DefineClass @consonants = /^dv.*A$/;
    IMatra @consonants : dvmI -> /^dvmI/;

For more on how this plugin actually operates, see :ref:`imatra`.
"""

import fontFeatures
import warnings

GRAMMAR = """
IMatra_Args = glyphselector:bases ws ':' ws glyphselector:matra ws '->' ws glyphselector:matras -> (bases,matra,matras)
"""

VERBS = ["IMatra"]


class IMatra:
    @classmethod
    def action(self, parser, bases, matra, matras):
        bases = bases.resolve(parser.fontfeatures, parser.font)
        matra = matra.resolve(parser.fontfeatures, parser.font)
        matras = matras.resolve(parser.fontfeatures, parser.font)

        # Organise matras into overhang widths
        matras2bases = {}
        matrasAndOverhangs = [
            (m, -parser.font[m].rightMargin) for m in matras
        ]
        for b in bases:
            w = self.find_stem(parser.font, b)
            warnings.warn("Stem location for %s: %s" % (b,w))
            (bestMatra, _) = min(matrasAndOverhangs, key=lambda s: abs(s[1] - w))
            if not bestMatra in matras2bases:
                matras2bases[bestMatra] = []
            matras2bases[bestMatra].append(b)
        rv = []
        for bestMatra, basesForThisMatra in matras2bases.items():
            rv.append(
                fontFeatures.Substitution(
                    [matra], postcontext=[basesForThisMatra], replacement=[[bestMatra]]
                )
            )
        return [fontFeatures.Routine(rules=rv)]

    @classmethod
    def find_stem(self, font, base):
        glyph = font[base]
        # Try stem anchors first
        possible = [a.x for a in glyph.anchors if a.name == "abvm.e" or a.name == "abvm" ]
        if possible:
            return possible[0]
        # Try a right margin
        if "dvmE" in font:
            margin = [a.x for a in font["dvmE"].anchors if a.name == "_abvm.e" or a.name == "_abvm" ]
            if margin:
                return glyph.width - margin[0]
        return glyph.width / 2
