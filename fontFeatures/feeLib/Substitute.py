import fontFeatures

GRAMMAR = """
Substitute_Args = gsws+:l ws '->' ws? (gsws | dollar_gs)+:r languages?:languages -> (l,r,languages)
gsws = glyphselector:g ws? -> g
dollar_gs = '$' integer:d glyphsuffix*:g ws? -> { "reference": d, "suffixes": g }
languages = '<' lang '/' script (ws ',' ws lang '/' script)* '>' ws
lang = letter{3,4} | '*' # Fix later
script = letter{3,4} | '*' # Fix later
"""

VERBS = ["Substitute"]

class Substitute:
    @classmethod
    def action(self, parser, l, r, languages):
        inputs  = [g.resolve(parser.fontfeatures, parser.font) for g in l]
        for ix, output in enumerate(r):
        	if isinstance(output, dict):
        		r[ix] = l[output["reference"]-1]
        		if "suffixes" in output:
	        		r[ix].suffixes = output["suffixes"]
        outputs = [g.resolve(parser.fontfeatures, parser.font) for g in r]
        languages = None # For now
        return [fontFeatures.Substitution(inputs, outputs, languages=languages)]
