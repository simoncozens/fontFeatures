# Code for converting a Substitution object into feaLib statements
import fontTools.feaLib.ast as feaast
from fontFeatures.ttLib.Substitution import lookup_type


def glyphref(g):
    if len(g) == 1:
        return feaast.GlyphName(g[0])
    return feaast.GlyphClass([feaast.GlyphName(x) for x in g])


def asFeaAST(self):
    lut = lookup_type(self)
    if lut == 3:
        return feaast.AlternateSubstStatement(
            [glyphref(x) for x in self.precontext],
            glyphref(self.input[0]),
            [glyphref(x) for x in self.postcontext],
            feaast.GlyphClass([feaast.GlyphName(x) for x in self.replacement[0]]),
        )
    elif lut == 1:
        return feaast.SingleSubstStatement(
            [glyphref(x) for x in self.input],
            [glyphref(x) for x in self.replacement],
            [glyphref(x) for x in self.precontext],
            [glyphref(x) for x in self.postcontext],
            False,
        )
    elif lut == 4:
        return feaast.LigatureSubstStatement(
            [glyphref(x) for x in self.precontext],
            [glyphref(x) for x in self.input],
            [glyphref(x) for x in self.postcontext],
            glyphref(self.replacement[0]),
            False,
        )
    elif lut == 8:
        return feaast.ReverseChainSingleSubstStatement(
            [glyphref(x) for x in self.precontext],
            [glyphref(x) for x in self.postcontext],
            [glyphref(x) for x in self.input],
            [glyphref(self.replacement[0])],
        )
    elif lut == 9:
        raise ValueError
    elif lut == 2:
        return feaast.MultipleSubstStatement(
            [glyphref(x) for x in self.precontext],
            glyphref(self.input[0]),
            [glyphref(x) for x in self.postcontext],
            [glyphref(x) for x in self.replacement],
        )

    import warnings

    warnings.warn("Couldn't convert Substitution Lookup Type %i" % lut)
    raise ValueError()
