"""
Medial Ra selection
===================

Same as IMatra, but for Myanmar::

    LoadPlugin MedialRa;
    DefineClass @consonants = /^{1,3}a$/;
    MedialRa @consonants : medial-ra -> @otherras;

"""

import fontFeatures
from . import FEEVerb

PARSEOPTS = dict(use_helpers=True)
GRAMMAR = """
?start: action
action: glyphselector ":" glyphselector integer_container? "->" glyphselector
"""

VERBS = ["MedialRa"]


class MedialRa(FEEVerb):
    def action(self, args):
        parser = self.parser
        bases = args[0].resolve(parser.fontfeatures, parser.font)
        medialra = args[1].resolve(parser.fontfeatures, parser.font)
        if len(args) == 3:
            otherras = args[2].resolve(parser.fontfeatures, parser.font)
            overshoot = 0
        else:
            overshoot = args[2]
            otherras = args[3].resolve(parser.fontfeatures, parser.font)

        # Chuck the original ra in the basket
        if overshoot is None:
            overshoot = 0
        ras = set(otherras + medialra)

        # Organise ras into overhang widths
        ras2bases = {}
        rasAndOverhangs = [(m, -parser.font[m].rightMargin+overshoot) for m in ras]
        rasAndOverhangs = list(reversed(sorted(rasAndOverhangs)))

        for b in bases:
            w = parser.font[b].width - ((parser.font[b].rightMargin or 0) + (parser.font[b].leftMargin or 0))
            bestRa = None
            for ra, overhang in rasAndOverhangs:
                if overhang <= w:
                    bestRa = ra
                    break
            if not bestRa:
                continue
            if bestRa not in ras2bases:
                ras2bases[bestRa] = []
            ras2bases[bestRa].append(b)
        rv = []
        for bestRa, basesForThisRa in ras2bases.items():
            rv.append(
                fontFeatures.Substitution(
                    [medialra], postcontext=[basesForThisRa], replacement=[[bestRa]]
                )
            )
        return [fontFeatures.Routine(rules=rv)]
