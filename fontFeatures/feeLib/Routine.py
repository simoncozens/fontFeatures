"""
Routine
=======

To group a set of rules into a routine, use the ``Routine`` verb. This takes
a name and a block containing rules::

    Routine {
        ...
    };

Note that in FEE syntax you must not repeat the routine name at the end of
the block, as is required in AFDKO syntax. Instead, any routine flags are
added to the end of the block, and may be any combination of ``RightToLeft``;
``IgnoreBases`` (AFDKO users, note the changed name); ``IgnoreLigatures``;
``IgnoreMarks`` or ``UseMarkFilteringSet`` followed by a glyph selector.

In simple cases, you do not need to wrap rules in a routine inside of a feature
block; however, to combine rules with different flags, you must place the rules
within a routine. Once you have placed one set of rules within a routine, you
may find it less surprising to place all rulesets within a feature within their
own routines as well, due to the way that OpenType orders lookups for processing.
"""

GRAMMAR = """
Routine_Args = routinename?:f wsc routine_tail?:tail wsc -> (f,tail)
routine_tail =  '{' wsc statement+:s '}' wsc flag*:flags -> (s, flags)

routinename = <(letter|digit|"_")+>

rl  = "RightToLeft"         -> 0x1
ib  = "IgnoreBases"         -> 0x2
il  = "IgnoreLigatures"     -> 0x4
im  = "IgnoreMarks"         -> 0x8
mat = "MarkAttachmentType"  -> 0xFF00
umf = "UseMarkFilteringSet" -> 0x10
flag = ( rl | ib | il | im |  complexflag):f ws -> f
complexflag = (umf|mat):value ws glyphselector:gs -> (value,gs)
"""
VERBS = ["Routine"]

import fontFeatures

class Routine:
    @classmethod
    def action(self, parser, routinename, tail):
        if not tail:
            rr = fontFeatures.RoutineReference(name = routinename)
            return [rr]
        statements, flags = tail;
        r = fontFeatures.Routine()
        if routinename:
          r.name = routinename
        r.rules = []
        for res in parser.filterResults(statements):
          if isinstance(res, fontFeatures.Routine):
            r.rules.extend(res.rules)
          else:
            r.rules.append(res)
        r.flags = 0
        for f in flags:
          if isinstance(f, tuple):
            r.flags |= f[0]
            if f[0] == 0x10:
              r.markFilteringSet = f[1].resolve(parser.fontfeatures, parser.font)
            elif f[0] == 0xFF00:
              r.markAttachmentSet = f[1].resolve(parser.fontfeatures, parser.font)
          else:
            r.flags |= f
        if not parser.current_feature:
          parser.fontfeatures.routines.append(r)
        return [r]
