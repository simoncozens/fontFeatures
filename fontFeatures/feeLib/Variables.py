"""
Variables
=========

Numbers can be stored in variables using the ``Set`` verb.

Examples::
    Set $spacing = 150;
    Position A $spacing B;

"""

import lark

PARSEOPTS = dict(use_helpers=True)

GRAMMAR = """
    ?start: action
    action: BARENAME "=" SIGNED_NUMBER

    %ignore WS
"""

VERBS = ["Set"]

class Set(lark.Transformer):
    def __init__(self, parser):
        self.parser = parser

    def action(self, args):
        self.parser.variables[args[0].value] = args[1].value
        return (args[0].value, args[1].value)
