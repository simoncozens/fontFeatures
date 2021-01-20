"""
Ligature Finder
===============

Looks for ligature glyphs matching a glyph selector and tries to write ligature rules
which compose them. e.g. given::

    LoadPlugin LigatureFinder;
    Routine ligatures {
        LigatureFinder /kinzi.*/;
    };

If you have glyphs `kinzi_ai`, `kinzi` and `ai`, this will write a rule
`Substitute kinzi ai -> kinzi_ai;`.
"""

import fontFeatures

GRAMMAR = """
LigatureFinder_Args = glyphselector:g -> (g,)
"""
import re

VERBS = ["LigatureFinder"]

class LigatureFinder:
    @classmethod
    def action(cls, parser, ligatures):
        ligatures = sorted(ligatures.resolve(parser.fontfeatures, parser.font),key=lambda a:len(a))
        rv = []
        glyphnames = "|".join(sorted(parser.font.keys(),key=lambda a:len(a)))
        for l in ligatures:
            for liglen in range(5,0,-1):
                ligre = "^" + ("("+glyphnames+")_") * liglen + "(" + glyphnames + ")$"
                m = re.match(ligre, l)
                if m:
                    rv.append(fontFeatures.Substitution(
                            [ [c] for c in m.groups()], replacement=[[l]]
                        ))
                    break
        return [fontFeatures.Routine(rules=rv)]
