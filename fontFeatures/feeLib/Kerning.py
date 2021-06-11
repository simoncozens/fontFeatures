"""
Kerning
=======

The ``Kerning`` plugin provides the ``Kerning`` verb. This reads the kerning
information from the source file and outputs kerning rules.

    Feature kern {
        Kerning;
    }

The ``Kerning`` verb takes one optional parameters: a glyph selector to
match particular glyphs. If any glyph in either of the classes in either side
of the kern pair matches, then the rule is emitted; if not, it is not. The
idea of this parameter is to allow you to split your kerning rules by script.

    Feature kern {
        Kerning /(?!.*-ar$)/; # Non-Arabic kerns go into kern
    };

    Feature dist {
        Kerning /-ar$/; # Arabic kerns go into dist
    };

"""

from . import FEEVerb
import fontFeatures
import warnings

PARSEOPTS = dict(use_helpers=True)

GRAMMAR = """
?start: action
action: glyphselector?
"""

VERBS = ["Kerning"]

class Kerning(FEEVerb):
    def action(self, args):
        glyphselector = args and args[0].resolve(self.parser.fontfeatures, self.parser.font)
        rules = []
        kerning = self.parser.font.default_master.kerning
        # XXX variable
        for ((l,r),kern) in kerning.items():
            # extend classes
            if l.startswith("@"):
                if not l[1:] in self.parser.font.features.namedClasses:
                    warnings.warn(f"Left kerning group '{l}' not found")
                    continue
                l = self.parser.font.features.namedClasses[l[1:]]
            else:
                l = [l]
            if r.startswith("@"):
                if not r[1:] in self.parser.font.features.namedClasses:
                    warnings.warn(f"Right kerning group '{r}' not found")
                    continue
                r = self.parser.font.features.namedClasses[r[1:]]
            else:
                r = [r]
            # XXX split mark/base?
            if glyphselector and not any(glyph in glyphselector for glyph in l+r):
                continue
            rules.append(fontFeatures.Positioning(
                [l,r],
                [ fontFeatures.ValueRecord(xAdvance=kern), fontFeatures.ValueRecord() ],
                flags=0x8
            ))
        return rules


