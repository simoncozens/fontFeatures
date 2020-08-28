"""
Substitute
==========

Substitution rules are created using the ``Substitute`` verb. There are two
forms of this verb:

- a simple substitution, which simply has a number of glyph
  selectors on each side of an arrow (``->``)
- a contextual substitution, which wraps the main glyphs to be substituted in
  curly braces, and optionally surrounds them with prefix and/or suffix glyphs.

Examples::

    Substitute f i -> f_i;

    Substitute [CH_YEu1 BEu1] { NUNu1 } -> NUNf2;

Within the right hand side of a ``Substitute`` operation, you may use
*backreferences* as glyph selectors to refer to glyph selectors in equivalent
positions on the left hand side. For example, the following rule::

    Substitute [a e i o u] comma -> $1;

is equivalent to::

    Substitute [a e i o u] comma -> [a e i o u];

The ``ReverseSubstitute`` verb is equivalent but creates reverse chaining
substitution rules.
"""

import fontFeatures

GRAMMAR = """
Substitute_Args = context_sub_args | normal_sub_args
ReverseSubstitute_Args = glyphselector:l ws '->' ws? (gsws | dollar_gs):r languages?:languages -> ([l],[r],languages)

normal_sub_args = gsws+:l '->' ws? (gsws | dollar_gs)+:r languages?:languages -> (l,r,languages, [], [])
context_sub_args = gsws*:pre '{' ws gsws+:l2 ws '}' ws gsws*:post '->' ws (gsws | dollar_gs)+:r languages?:languages -> (l2,r,languages, pre, post)


gsws = glyphselector:g ws? -> g
dollar_gs = '$' integer:d glyphsuffix*:g ws? -> { "reference": d, "suffixes": g }
languages = '<' lang '/' script (ws ',' ws lang '/' script)* '>' ws
lang = letter{3,4} | '*' # Fix later
script = letter{3,4} | '*' # Fix later
"""

VERBS = ["Substitute", "ReverseSubstitute"]

class Substitute:
    @classmethod
    def action(self, parser, l, r, languages, pre, post):
        inputs  = [g.resolve(parser.fontfeatures, parser.font) for g in l]
        pre     = [g.resolve(parser.fontfeatures, parser.font) for g in pre]
        post     = [g.resolve(parser.fontfeatures, parser.font) for g in post]
        for ix, output in enumerate(r):
        	if isinstance(output, dict):
        		r[ix] = l[output["reference"]-1]
        		if "suffixes" in output:
	        		r[ix].suffixes = output["suffixes"]
        outputs = [g.resolve(parser.fontfeatures, parser.font) for g in r]
        languages = None # For now
        return [fontFeatures.Substitution(inputs, outputs,
            precontext = pre,
            postcontext = post,
            languages=languages)]

class ReverseSubstitute(Substitute):
    @classmethod
    def action(self, parser, l, r, languages):
        s = super().action(parser,l,r,languages,[],[])
        s[0].reverse = True
        return s
