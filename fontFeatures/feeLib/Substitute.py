import fontFeatures

GRAMMAR = """
Substitute_Args = Substitute_gsws+:l ws '->' ws? Substitute_gsws+:r -> (l,r)
Substitute_gsws = glyphselector:g ws? -> g
"""

VERBS = ["Substitute"]

class Substitute:
    @classmethod
    def action(self, parser, l, r):
        inputs  = [g.resolve(parser.fontfeatures, parser.font) for g in l]
        outputs = [g.resolve(parser.fontfeatures, parser.font) for g in r]
        languages = None # For now
        return [fontFeatures.Substitution(inputs, outputs, languages=languages)]
