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
from .Substitute import BASE_GRAMMAR, Substitute_GRAMMAR, Substitute
from .util import extend_args_until

PARSEOPTS = dict(use_helpers=True)

Position_GRAMMAR = Substitute_GRAMMAR

GRAMMAR = BASE_GRAMMAR+"""
gspos: glyphselector valuerecord?
gsposes: gspos+
normal_action: gsposes maybe_languages
maybe_languages: languages?
contextual_action: pre "(" normal_action ")" post
"""

VERBS = ["Position"]

def makeValueRecord(valuerecord):
    if not isinstance(valuerecord, dict):
        return ValueRecord(*valuerecord) # Traditional -> list
    v = ValueRecord()
    for k in valuerecord["members"]:
        setattr(v,k["dimension"],k["position"])
    return v

class Position(Substitute):
    def contextual_action(self, args):
        args = extend_args_until(args, 4)
        (pre, stuff, languages, post) = args
        args = [stuff, languages, pre, post]
        return args

    def normal_action(self, args):
        return args

    def valuerecord(self, args):
        return args[0]

    fea_value_record = normal_action
    maybe_languages = normal_action
    gsposes = normal_action

    def fee_value_record(self, args):
        ret = []
        while len(args) > 0:
            verb = args.pop(0)
            value = args.pop(0)
            ret.append({"dimension": verb, "position": value})

        return {"members": ret}

    def gspos(self, args):
        # If no valuerecord, append a None
        if len(args) == 1:
            args.append(None)
        return args

    def action(self, args):
        args = args[0]
        args = extend_args_until(args, 4)
        (l, languages, pre, post) = args

        inputs = []
        valuerecords = []
        pre     = [g.resolve(self.parser.fontfeatures, self.parser.font) for g in pre]
        post     = [g.resolve(self.parser.fontfeatures, self.parser.font) for g in post]
        for glyphselector, valuerecord in l:
            inputs.append(glyphselector.resolve(self.parser.fontfeatures, self.parser.font))
            if valuerecord:
                valuerecords.append(makeValueRecord(valuerecord))
            else:
                valuerecords.append(None)
        languages = None # For now
        return [Positioning(inputs, valuerecords,
            precontext = pre,
            postcontext = post,
            languages=languages)]

