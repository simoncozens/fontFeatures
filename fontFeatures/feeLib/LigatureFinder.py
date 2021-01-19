"""
Ligature Finder
===============

Looks for ligature glyphs matching a glyph selector and tries to write ligature rules
which compose them. e.g. given

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

VERBS = ["LigatureFinder"]


class LigatureFinder:
    @classmethod
    def action(cls, parser, ligatures):
        ligatures = ligatures.resolve(parser.fontfeatures, parser.font)
        rv = []
        for l in ligatures:
            components = l.split("_")
            if len(components) > 1 and all(c in parser.font.keys() for c in components):
                rv.append(fontFeatures.Substitution(
                        [ [c] for c in components], replacement=[[l]]
                    ))
        return [fontFeatures.Routine(rules=rv)]
