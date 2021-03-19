"""
Delete
======

Deletes a glyph from the glyphstream:

Examples::

    Routine DeleteUMark { Delete UMark; };
    Routine MedialRaToRaU { Substitute medialRa-myanmar -> medialRa_uMark-myanmar; };
    Chain (medialRa-myanmar ^MedialRaToRaU @Consonant uMark-myanmar ^DeleteUMark);

"""

import fontFeatures
from . import FEEVerb
from .util import extend_args_until

PARSEOPTS = dict(use_helpers=True)

# A different variable is used so Chain.py can import it and redefine pre/left/post/right
GRAMMAR = """
?start: action
action: glyphselector
"""
VERBS = ["Delete"]

class Delete(FEEVerb):
    def action(self, args):
        glyph  = args[0].resolve(self.parser.fontfeatures, self.parser.font)
        return [fontFeatures.Substitution(
          [glyph],
          []
        )]
