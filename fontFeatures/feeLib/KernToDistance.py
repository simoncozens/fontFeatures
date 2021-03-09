# This is a good idea but needs a bit of rethinking.

from fontFeatures.feeLib import FEEVerb
from glyphtools import determine_kern, bin_glyphs_by_metric
import fontFeatures
import itertools
from fontFeatures.feeLib.util import extend_args_until


PARSEOPTS = dict(use_helpers=True)

GRAMMAR = """
?start: action
action: normal_action | contextual_action
normal_action: glyphselector glyphselector integer_container
contextual_action: pre "(" glyphselector glyphselector ")" integer_container
pre: glyphselector*
"""

VERBS = ["KernToDistance"]


class KernToDistance(FEEVerb):
    def contextual_action(self, args):
        args = extend_args_until(args, 4)
        (pre, l, r, languages) = args
        args = [l, r, languages, pre]
        return args

    def pre(self, args):
        return args

    def normal_action(self, args):
        args = extend_args_until(args, 4)
        return args

    def action(self, args):
        parser = self.parser
        bincount = 5
        lefts, rights, units, pre = args[0]
        lefts = lefts.resolve(parser.fontfeatures, parser.font)
        rights = rights.resolve(parser.fontfeatures, parser.font)
        pre = [ g.resolve(parser.fontfeatures, parser.font) for g in pre ]

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

        if not pre:
            return [fontFeatures.Routine(rules=make_kerns())]

        kerns = []
        binned_contexts = [
            bin_glyphs_by_metric(parser.font, glyphs, "rise", bincount=bincount)
            for glyphs in pre
        ]
        for c in itertools.product(*binned_contexts):
            totalrise = sum([x[1] for x in c])
            precontext = [x[0] for x in c]
            kerns.extend(make_kerns(totalrise, context=precontext, direction="RTL"))

        return [fontFeatures.Routine(rules=kerns)]
