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

GRAMMAR = """
If_Args = boolean_condition:c wsc '{' wsc statement+:s wsc '}' -> (c,s)
boolean_condition = or | and | boolean_term
boolean_term = bracketed | not | boolean_factor
boolean_factor = integer:l ws comparison?:r -> parser.plugin_classes["If"].docomparison(l,r)
comparison = ('>='|'>'|'<='|'<'|'=='|'!='):cmp ws integer:r -> (cmp,r)
not = "not" ws boolean_condition:b -> not bool(b)
bracketed = "(" ws boolean_condition:b ws ")" -> b
or = boolean_term:a ws "or" ws boolean_term:b -> (a or b)
and = boolean_term:a ws "and" ws boolean_term:b -> (a and b)
"""

VERBS = ["If"]

class If:
    @classmethod
    def action(self, parser, condition, statements):
        if bool(condition):
            return parser.filterResults(statements)
        else:
            return []

    @classmethod
    def docomparison(self, l,r):
        if not r:
            return bool(l)
        left,operator, right = l,r[0],r[1]
        if operator == "<":
            return left < right
        if operator == "<=":
            return left < right
        if operator == "==":
            return left == right
        if operator == ">":
            return left > right
        if operator == ">=":
            return left >= right
        if operator == "!=":
            return left != right
