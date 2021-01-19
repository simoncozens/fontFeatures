# Code for converting a Substitution object into feaLib statements
import fontTools.feaLib.ast as feaast
from fontFeatures.ttLib.Substitution import lookup_type
from itertools import cycle


def glyphref(g):
    if len(g) == 1:
        return feaast.GlyphName(g[0])
    return feaast.GlyphClass([feaast.GlyphName(x) for x in g])


def is_paired(self):
    # One of the substitution/replacements has all-but-one arity one,
    # and both arities are the same
    input_lengths = [len(x) for x in self.input if len(x) != 1]
    replacement_lengths = [len(x) for x in self.replacement if len(x) != 1]
    if not (len(input_lengths) == 1 and len(replacement_lengths) ==1):
        return False
    if input_lengths[0] != replacement_lengths[0]:
        import warnings
        warnings.warn("Unbalanced paired substitution")
        return False
    return True

def paired_ligature(self):
    b = feaast.Block()
    inputs = []
    for i in self.input:
        if len(i) == 1:
            inputs.append(cycle(i))
        else:
            inputs.append(i)
    lhs = zip(*inputs)
    replacements = []
    for j in self.replacement:
        if len(j) == 1:
            replacements.append(cycle(j))
        else:
            replacements.append(j)
    rhs = zip(*replacements)
    for l, r in zip(lhs,rhs):
        b.statements.append(
            feaast.LigatureSubstStatement(
            [glyphref(x) for x in self.precontext],
            [glyphref([x]) for x in l],
            [glyphref(x) for x in self.postcontext],
            glyphref([r[0]]),
            False,
        )
        )
    return b

def asFeaAST(self):
    lut = lookup_type(self)
    if not lut:
        return feaast.Comment("")
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
        # Paired rules need to become a set of statements
        if is_paired(self):
            return paired_ligature(self)

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
