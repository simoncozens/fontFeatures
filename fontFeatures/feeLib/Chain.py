"""
Chain
==========

Chaining rules are created using the ``Chain`` verb.

Examples::

    Chain glyph1 (lookup1) glyph2 (lookup2);
    Chain pre { glyph1 (lookup1,lookup2) glyph2  glyph3 (lookup3) } post;

"""

import fontFeatures

GRAMMAR = """
Chain_Args = normal_chain_args | contextual_chain_args

normal_chain_args = gsluws+:stuff languages?:languages -> (stuff,languages, [], [])
contextual_chain_args =  gsws*:pre '{' gsluws+:stuff languages?:languages '}' ws gsws*:post -> (stuff,languages, pre, post)
gsluws = glyphselector:g ws lookup_list?:l ws -> (g,l)
lookup_list = '(' ws lookups:l ws ')' -> l
lookups = lookup*
lookup = barename:b ws? ','? -> b["barename"]
languages = '<' lang '/' script (ws ',' ws lang '/' script)* '>' ws
lang = letter{3,4} | '*' # Fix later
script = letter{3,4} | '*' # Fix later
"""

VERBS = ["Chain"]

class Chain:
    @classmethod
    def action(self, parser, stuff, languages, pre, post):
        inputs  = [x[0].resolve(parser.fontfeatures, parser.font) for x in stuff]
        lookupnames = [x[1] or [] for x in stuff]
        lookups = []
        for lu in lookupnames:
            lookups.append([fontFeatures.RoutineReference(name=x) for x in lu])
        pre     = [g.resolve(parser.fontfeatures, parser.font) for g in pre]
        post     = [g.resolve(parser.fontfeatures, parser.font) for g in post]
        languages = None # For now
        return [fontFeatures.Chaining(inputs, lookups = lookups,
            precontext = pre,
            postcontext = post,
            languages=languages)]
