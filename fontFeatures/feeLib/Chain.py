"""
Chain
==========

Chaining rules are created using the ``Chain`` verb. Lookups are differentiated
from glyph selectors by prepending a ``^``.

Examples::

    Chain glyph1 ^lookup1 glyph2 ^lookup2;
    Chain pre ( glyph1 ^lookup1,^lookup2 glyph2 glyph3 ^lookup3 ) post;

"""

import fontFeatures
from .Substitute import BASE_GRAMMAR, Substitute_GRAMMAR, Substitute

PARSEOPTS = dict(use_helpers=True)

Chain_GRAMMAR = Substitute_GRAMMAR

GRAMMAR = BASE_GRAMMAR+"""
lookup: "^" BARENAME ","?
lookups: lookup*
gslu: glyphselector lookups
gslu_list: gslu+

normal_action: gslu_list languages?
contextual_action: pre "(" normal_action ")" post
"""

VERBS = ["Chain"]

class Chain(Substitute):
    def lookups(self, args):
        return args

    def gslu(self, args):
        # If no lookup list, append a None
        if len(args) == 1:
            args.append(None)
        return args

    def lookup(self, args):
        (lookupname,) = args

        return lookupname.value

    def contextual_action(self, args):
        return args

    gslu_list = contextual_action

    def normal_action(self, args):
        if len(args) == 1: # No languages provided
            args.append(None)
        return args

    # stuff, languages, pre, post
    def action(self, args):
        # `stuff` are tuples of (glyphselector, lookup_list)
        (pre, (stuff, languages), post) = args[0]

        inputs  = [x[0].resolve(self.parser.fontfeatures, self.parser.font) for x in stuff]
        lookupnames = [x[1] or [] for x in stuff]
        lookups = []
        for lu in lookupnames:
            lookups.append([fontFeatures.RoutineReference(name=x) for x in lu])
        pre     = [g.resolve(self.parser.fontfeatures, self.parser.font) for g in pre]
        post     = [g.resolve(self.parser.fontfeatures, self.parser.font) for g in post]
        return [fontFeatures.Chaining(inputs, lookups = lookups,
            precontext = pre,
            postcontext = post,
            languages=languages)]
