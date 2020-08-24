# Code for converting a Chaining object into feaLib statements
import fontTools.feaLib.ast as feaast
import fontFeatures


# Can we chain multiple lookups?
from fontTools.feaLib.parser import Parser
import io

teststring = (
    "lookup l1 { } l1; lookup l2 { } l2; lookup a { sub a' lookup l1 lookup l2; } a;"
)
parsetree = Parser(io.StringIO(teststring), ()).parse()
if "\\" in parsetree.asFea():
    EXPERIMENTAL_FONTTOOLS = False
else:
    EXPERIMENTAL_FONTTOOLS = True


def glyphref(g):
    if len(g) == 1:
        return feaast.GlyphName(g[0])
    return feaast.GlyphClass([feaast.GlyphName(x) for x in g])


def suborpos(lookups):
    for l in lookups:
        if not l:
            continue
        for aLookup in l:
            if not aLookup:
                continue
            for r in aLookup.rules:
                if isinstance(r, fontFeatures.Substitution):
                    return "sub"
                if isinstance(r, fontFeatures.Positioning):
                    return "pos"
                if isinstance(r, fontFeatures.Attachment):
                    return "pos"
                if isinstance(r, fontFeatures.Chaining):
                    return suborpos(r.lookups)


def gensym(ff):
    if not "index" in ff.scratch:
        ff.scratch["index"] = 0
    ff.scratch["index"] = ff.scratch["index"] + 1
    return str(ff.scratch["index"])


def replaceLongWithClasses(i, ff):
    for ix, gc in enumerate(i):
        if len(gc) > 5:
            classname = ff.getNamedClassFor(sorted(gc), "class" + gensym(ff))
            i[ix] = ["@" + classname]


def feaPreamble(self, ff):
    if not "glyphclasses" in ff.scratch:
        ff.scratch["glyphclasses"] = {tuple(sorted(ff.namedClasses[g])): g for g in ff.namedClasses.keys()}
    replaceLongWithClasses(self.input, ff)
    replaceLongWithClasses(self.precontext, ff)
    replaceLongWithClasses(self.postcontext, ff)

    from fontFeatures.optimizer.FontFeatures import MergeNonOverlappingRoutines

    rv = []

    if EXPERIMENTAL_FONTTOOLS == False:
        ff.markRoutineUseInChains()
        if not "synthesised_lookups" in ff.scratch:
            ff.scratch["synthesised_lookups"] = {}
        for ix, lookuplist in enumerate(self.lookups):
            if not lookuplist:
                continue

            if len(lookuplist) == 2:  # Test purposes
                synthname = lookuplist[0].name + "_" + lookuplist[1].name
                synthname2 = lookuplist[1].name + "_" + lookuplist[0].name
                if synthname in ff.scratch["synthesised_lookups"]:
                    self.lookups[ix] = [ff.scratch["synthesised_lookups"][synthname]]
                elif synthname2 in ff.scratch["synthesised_lookups"]:
                    self.lookups[ix] = [ff.scratch["synthesised_lookups"][synthname2]]
                else:
                    o = MergeNonOverlappingRoutines()
                    if o.compatibleRules(lookuplist[0], lookuplist[1]):
                        synthesised = fontFeatures.Routine()
                        synthesised.rules.extend(lookuplist[0].rules)
                        synthesised.rules.extend(lookuplist[1].rules)
                        synthesised.name = synthname
                        from fontFeatures.optimizer import Optimizer

                        Optimizer().optimize_routine(synthesised)
                        self.lookups[ix] = [synthesised]
                        ff.scratch["synthesised_lookups"][synthname] = synthesised
                        rv.append(synthesised.asFeaAST())
    return rv


def _complex(self):
    import warnings

    if EXPERIMENTAL_FONTTOOLS:
        if suborpos(self.lookups) == "sub":
            routine = feaast.ChainContextSubstStatement
        else:
            routine = feaast.ChainContextPosStatement

        return routine(
            [glyphref(x) for x in self.precontext],
            [glyphref(x) for x in self.input],
            [glyphref(x) for x in self.postcontext],
            self.lookups,
        )
    else:
        warnings.warn("Can't currently express multiple lookups per position in AFDKO")
        return feaast.Comment("# Unparsing failed")


def asFeaAST(self):
    if len(self.lookups) > 0 and any([x is not None for x in self.lookups]):
        # Fill in the blanks
        if suborpos(self.lookups) == "sub":
            routine = feaast.ChainContextSubstStatement
        else:
            routine = feaast.ChainContextPosStatement
        # Check for >1 lookups per position
        if any([x and len(x) > 1 for x in self.lookups]):
            return _complex(self)
        if EXPERIMENTAL_FONTTOOLS:
            lookups = self.lookups
        else:
            self.lookups = [x or [None] for x in self.lookups]
            lookups = [l[0] for l in self.lookups]
        return routine(
            [glyphref(x) for x in self.precontext],
            [glyphref(x) for x in self.input],
            [glyphref(x) for x in self.postcontext],
            lookups,
        )
    else:
        return feaast.IgnoreSubstStatement(
            chainContexts=[
                [
                    [glyphref(x) for x in self.precontext],
                    [glyphref(x) for x in self.input],
                    [glyphref(x) for x in self.postcontext],
                ]
            ]
        )


def asFea(self):
    return self.asFeaAST().asFea()
