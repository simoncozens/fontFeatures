"""
Variables
=========

Numbers can be stored in variables using the ``Set`` verb.

Examples::

    Set $spacing = 150;
    Position A $spacing B;

"""

import fontFeatures

GRAMMAR = """
Set_Args = '$' barename:b ws '=' ws integer:v -> (b,v)
"""

VERBS = ["Set"]

class Set:
    @classmethod
    def action(self, parser, b,v):
        parser.variables[b["barename"]] = v
        return []
