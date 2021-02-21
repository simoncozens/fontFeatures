"""
Conditional
===========

Rules can be applied conditionally using the `If` statement. These will make
more sense when you can define variables.

Examples::

    If $dosub {
        Substitute a -> b;
    }

"""

import fontFeatures
from .util import compare
from . import FEEVerb

PARSEOPTS = dict(use_helpers=True)

GRAMMAR = """
boolean_condition: comparison | (boolean_term | not_boolean_term)
boolean_term: integer_container COMPARATOR integer_container
not_boolean_term: "not" boolean_term
comparison: (boolean_term | not_boolean_term) AND_OR (boolean_term | not_boolean_term)
AND_OR: ("&" | "|")
"""

If_GRAMMAR = """
?start: action
action: boolean_condition "{" statement+ "}"
"""

If_beforebrace_GRAMMAR = """
?start: beforebrace
beforebrace: boolean_condition
"""

VERBS = ["If"]

class If(FEEVerb):
    def __init__(self, parser):
        self.parser = parser

    def comparison(self, args):
        (l, comparator, r) = args
        if comparator.value == "&":
            return l and r
        elif comparator.value == "|":
            return l or r
        else:
            raise ValueError("Unrecognized comparator")

    def boolean_term(self, args):
        (l, comparator, r) = args
        return compare(l, comparator, r)

    def boolean_condition(self, args):
        return args[0]

    def not_boolean_term(self, args):
        (boolean_term,) = args
        return not boolean_term

    def action(self, args):
        (boolean, statements, _) = args

        if bool(boolean):
            return statements
        else:
            return []
