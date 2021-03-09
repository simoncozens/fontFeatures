"""
Swap
====

Swaps two adjacent glyphs::

  Swap A B;

"""

import fontFeatures
from . import FEEVerb

PARSEOPTS = dict(use_helpers=True)

GRAMMAR = """
    ?start: action
    action: normal_action | contextual_action
    normal_action: glyphselector glyphselector
    contextual_action: pre "(" glyphselector glyphselector ")" post
    pre: glyphselector*
    post: glyphselector*
"""

VERBS = ["Swap"]

class Swap(FEEVerb):
    def normal_action(self, args):
        return [None, *args, None]

    def pre(self, args):
        if len(args) > 0:
            return args
        else:
            return None

    post = pre

    def contextual_action(self, args):
        (pre, l, r, post) = args
        return [pre, l, r, post]

    def action(self, args):
        (pre, l, r, post) = args[0]
        left  = l.resolve(self.parser.fontfeatures, self.parser.font)
        right = r.resolve(self.parser.fontfeatures, self.parser.font)
        precontext = None
        postcontext = None
        if pre:
            precontext = [g.resolve(self.parser.fontfeatures, self.parser.font) for g in pre]
        if post:
            postcontext = [g.resolve(self.parser.fontfeatures, self.parser.font) for g in post]

        lefttoright = fontFeatures.Routine(rules=[fontFeatures.Substitution([left], [right])])
        righttoleft = fontFeatures.Routine(rules=[fontFeatures.Substitution([right], [left])])
        return [fontFeatures.Chaining(
          [left, right],
          lookups = [ [lefttoright], [righttoleft] ],
          precontext = precontext,
          postcontext = postcontext,
        )]
