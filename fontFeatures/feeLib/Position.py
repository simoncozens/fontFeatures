"""
Position
========

Positioning rules are created using the ``Position`` verb. There are two
forms of this verb:

- a simple positioning, which simply has one or more glyph selectors each
  optionally followed by a value record.
- a contextual positioning, which wraps the main glyphs and value records in
  curly braces, and optionally surrounds them with prefix and/or suffix glyphs.

A value record can be specified either as a bare integer, in which case it
represents an X advance adjustment, or a tuple of four integers surrounded by
angle brackets, representing X position, Y position, X advance and Y advance,
or as a dictionary-like structure surrounded by angle brackets, taking the form::

    '<' ( ("xAdvance"| "xPlacement" | "yAdvance" | "yPlacement") '=' integer)+ '>'

Here are examples of each form of the positioning verb::

    # Above nuktas followed by GAF or KAF glyphs should drop down
    # and to the right
    Position @above_nuktas <30 -70 0 0> /^[KG]AF/;

    # Initial forms will get more space if they have consecutive dotted glyphs
    # and appear after a word-final glyph.
    Position @endofword { @inits 200 } @below_dots @medis @below_dots;

    # Move marks back and up.
    Position @marks <xPlacement=-50 yPlacement=10>;

"""

from fontFeatures import Positioning, ValueRecord


GRAMMAR = """
Position_Args = context_pos_args | normal_pos_args

normal_pos_args = gsposws+:g_ps  languages?:languages -> (g_ps,languages, [], [])
context_pos_args = gsws*:pre '{' ws gsposws+:g_ps2 ws '}' ws gsws*:post languages?:languages -> (g_ps2,languages, pre, post)

gsposws = glyphselector:g ws valuerecord?:v ws? -> (g,v)
gsws = glyphselector:g ws? -> g

languages = '<' lang '/' script (ws ',' ws lang '/' script)* '>' ws
lang = letter{3,4} | '*' # Fix later
script = letter{3,4} | '*' # Fix later

"""

VERBS = ["Position"]

def makeValueRecord(valuerecord):
    if not isinstance(valuerecord, dict):
        return ValueRecord(*valuerecord) # Traditional -> list
    v = ValueRecord()
    for k in valuerecord["members"]:
        setattr(v,k["dimension"],k["position"])
    return v

class Position:
    @classmethod
    def action(self, parser, l, languages, pre, post):
        inputs = []
        valuerecords = []
        pre     = [g.resolve(parser.fontfeatures, parser.font) for g in pre]
        post     = [g.resolve(parser.fontfeatures, parser.font) for g in post]
        for glyphselector, valuerecord in l:
            inputs.append(glyphselector.resolve(parser.fontfeatures, parser.font))
            if valuerecord:
                valuerecords.append(makeValueRecord(valuerecord))
            else:
                valuerecords.append(None)
        languages = None # For now
        return [Positioning(inputs, valuerecords,
            precontext = pre,
            postcontext = post,
            languages=languages)]

