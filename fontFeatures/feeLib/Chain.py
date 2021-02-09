"""
Chain
==========

Chaining rules are created using the ``Chain`` verb.

Examples::

    Chain glyph1 (lookup1) glyph2 (lookup2);
    Chain pre { glyph1 (lookup1,lookup2) glyph2  glyph3 (lookup3) } post;

"""

import fontFeatures
from .Substitute import BASE_GRAMMAR, Substitute_GRAMMAR, Substitute
from .util import extend_args_until

PARSEOPTS = dict(use_helpers=True)

Chain_GRAMMAR = Substitute_GRAMMAR

GRAMMAR = BASE_GRAMMAR+"""
lookup: "^" BARENAME ","?
lookups: lookup*
gslu: glyphselector lookups

normal_action: gslu+ languages?
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
        args = extend_args_until(args, 4)
        (pre, stuff, languages, post) = args
        args = [stuff, languages, pre, post]
        return args

    def normal_action(self, args):
        return args

    # stuff, languages, pre, post
    def action(self, args):
        # `stuff` are tuples of (glyphselector, lookup_list)
        (stuff, languages, pre, post) = args[0]

        inputs  = [x[0].resolve(self.parser.fontfeatures, self.parser.font) for x in stuff]
        lookupnames = [x[1] or [] for x in stuff]
        lookups = []
        for lu in lookupnames:
            lookups.append([fontFeatures.RoutineReference(name=x) for x in lu])
        pre     = [g.resolve(self.parser.fontfeatures, self.parser.font) for g in pre]
        post     = [g.resolve(self.parser.fontfeatures, self.parser.font) for g in post]
        languages = None # For now
        return [fontFeatures.Chaining(inputs, lookups = lookups,
            precontext = pre,
            postcontext = post,
            languages=languages)]
