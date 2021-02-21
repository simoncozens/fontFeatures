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

PARSEOPTS = dict(use_helpers=True)

GRAMMAR = """
SIMPLE_FLAG: "RightToLeft" | "IgnoreBases" | "IgnoreLigatures" | "IgnoreMarks"
COMPLEX_FLAG: "MarkAttachmentType" | "UseMarkFilteringSet"
complexflag: COMPLEX_FLAG glyphselector
flag: SIMPLE_FLAG | complexflag
flags: flag*
ROUTINENAME: (LETTER|DIGIT|"_")+
"""

Routine_GRAMMAR = """
?start: action
action: ROUTINENAME? "{" statement+ "}" flags
"""

Routine_beforebrace_GRAMMAR = """
?start: beforebrace
beforebrace: ROUTINENAME?
"""

Routine_afterbrace_GRAMMAR = """
?start: afterbrace
afterbrace: flags
"""

VERBS = ["Routine"]

FLAGS = {
    "RightToLeft": 0x1,
    "IgnoreBases": 0x2,
    "IgnoreLigatures": 0x4,
    "IgnoreMarks": 0x8,
    "MarkAttachmentType": 0xFF00,
    "UseMarkFilteringSet": 0x10
}

import fontFeatures
from . import FEEVerb

class Routine(FEEVerb):
    def beforebrace(self, args):
        return args

    def afterbrace(self, args):
        return args[0]
    
    flags = beforebrace

    def complexflag(self, args):
        return (FLAGS[args[0].value], args[1])

    def flag(self, args):
        (flag,) = args

        if isinstance(flag, str):
            return FLAGS[flag]
        elif isinstance(flag, tuple):
            return flag

    def action(self, args):
        (routinename, statements, flags) = args

        if routinename is not None:
            routinename = routinename[0].value

        if flags is None: flags = []

        if not statements:
            rr = fontFeatures.RoutineReference(name = routinename)
            return [rr]
        r = fontFeatures.Routine()
        if routinename:
            r.name = routinename
        r.rules = []
        for res in self.parser.filterResults(statements):
            if isinstance(res, fontFeatures.Routine):
                r.rules.extend(res.rules)
            else:
                r.rules.append(res)
        r.flags = 0
        for f in flags:
            if isinstance(f, tuple):
                r.flags |= f[0]
                if f[0] == 0x10:
                    r.markFilteringSet = f[1].resolve(self.parser.fontfeatures, self.parser.font)
                elif f[0] == 0xFF00:
                    r.markAttachmentSet = f[1].resolve(self.parser.fontfeatures, self.parser.font)
            else:
                r.flags |= f
        if not self.parser.current_feature:
            self.parser.fontfeatures.routines.append(r)
        return [r]
