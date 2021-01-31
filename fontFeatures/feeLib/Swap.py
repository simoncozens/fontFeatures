"""
Swap
====

Swaps two adjacent glyphs::

  Swap A B;

"""

import fontFeatures

GRAMMAR = """
Swap_Args = simple_swap | contextual_swap
simple_swap = glyphselector:l ws glyphselector:r -> (l,r,None,None)
contextual_swap = gsws*:pre ws '{' ws glyphselector:l ws glyphselector:r ws '}' ws gsws*:post -> (l,r,pre,post)
gsws = glyphselector:g ws? -> g
"""

VERBS = ["Swap"]

class Swap:
    @classmethod
    def action(self, parser, l, r, pre, post):
        left  = l.resolve(parser.fontfeatures, parser.font)
        right = r.resolve(parser.fontfeatures, parser.font)
        precontext = None
        postcontext = None
        if pre:
            precontext = [g.resolve(parser.fontfeatures, parser.font) for g in pre]
        if post:
            postcontext = [g.resolve(parser.fontfeatures, parser.font) for g in post]

        lefttoright = fontFeatures.Routine(rules=[fontFeatures.Substitution([left], [right])])
        righttoleft = fontFeatures.Routine(rules=[fontFeatures.Substitution([right], [left])])
        return [fontFeatures.Chaining(
          [left, right],
          lookups = [ [lefttoright], [righttoleft] ],
          precontext = precontext,
          postcontext = postcontext,
        )]
