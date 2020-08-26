from fontTools.misc.py23 import *
import fontTools
from collections import OrderedDict
from .GTableUnparser import GTableUnparser
from itertools import groupby
import fontFeatures

# These are silly little functions which help to document the intent


def glyph(x):
    assert isinstance(x, str)
    return [x]


def singleglyph(x):
    return [glyph(x)]


class GSUBUnparser(GTableUnparser):
    lookupTypes = {
        1: "SingleSubstitution",
        2: "MultipleSubstitution",
        3: "AlternateSubstitution",
        4: "LigatureSubstitution",
        5: "ContextualSubstitution",
        6: "ChainingContextualSubstitution",
        7: "Extension",
        8: "ReverseContextualSubstitution",
    }

    def isChaining(self, lookupType):
        return lookupType >= 5

    def unparseContextualSubstitution(self, lookup):
        b = fontFeatures.Routine(
            name=self.getname(self.getname("ContextualSubstitution" + self.gensym()))
        )
        for sub in lookup.SubTable:
            if sub.Format == 1:
                self._unparse_contextual_sub_format1(sub, b, lookup)
            else:
                try:
                    inputs = self._invertClassDef(sub.ClassDef.classDefs, self.font)
                    for classId, ruleset in enumerate(sub.SubClassSet):
                        if not ruleset:
                            continue
                        rules = ruleset.SubClassRule
                        inputclass = inputs[classId]
                        for r in rules:
                            input_ = [inputclass] + [inputs[x] for x in r.Class]
                            lookups = self._unparse_lookups(r.SubstLookupRecord)
                            if len(lookups) <= len(input_):
                                lookups.extend(
                                    [None] * (1 + len(input_) - len(lookups))
                                )
                            if len(input_) == 0:
                                raise ValueError
                            b.addRule(
                                fontFeatures.Chaining(
                                    input_,
                                    [],
                                    [],
                                    lookups=lookups,
                                    address=self.currentLookup,
                                    flags=lookup.LookupFlag,
                                )
                            )
                except Exception as e:
                    self.unparsable(b, "Lookup type 5 (" + str(e) + ")", sub)

        return b, []

    def unparseReverseContextualSubstitution(self, lookup):
        b = fontFeatures.Routine(
            name=self.getname("ReverseContextualSubstitution" + self.gensym())
        )
        for sub in lookup.SubTable:
            prefix  = []
            outputs = []
            suffix  = []
            if hasattr(sub, "BacktrackCoverage"):
                for coverage in reversed(sub.BacktrackCoverage):
                    prefix.append(coverage.glyphs)
            if hasattr(sub, "LookAheadCoverage"):
                for i, coverage in enumerate(sub.LookAheadCoverage):
                    suffix.append(coverage.glyphs)
            outputs = [ sub.Substitute ]
            inputs =  [ sub.Coverage.glyphs ]
            b.addRule(
                fontFeatures.Substitution(
                    inputs,
                    outputs,
                    prefix,
                    suffix,
                    flags=lookup.LookupFlag,
                    reverse=True
                )
            )
        return b,[]

    def unparseChainingContextualSubstitution(self, lookup):
        b = fontFeatures.Routine(
            name=self.getname("ChainingContextualSubstitution" + self.gensym())
        )
        for sub in lookup.SubTable:
            if sub.Format == 1 or sub.Format == 3:
                self._unparse_contextual_chain_format1(sub, b, lookup)
            elif sub.Format == 2:
                self._unparse_contextual_format2(sub, b, lookup)
            else:
                raise ValueError
        return b, []

    def _unparse_contextual_sub_format1(self, sub, b, lookup):
        prefix = []
        inputs = []
        lookups = []
        suffix = []

        if hasattr(sub, "SubRuleSet"):
            for subrulesets, input_ in zip(sub.SubRuleSet, sub.Coverage.glyphs):
                for subrule in subrulesets.SubRule:
                    lookups = []
                    allinput = [glyph(x) for x in ([input_] + subrule.Input)]
                    lookups = self._unparse_lookups(subrule.SubstLookupRecord)
                    if len(lookups) <= len(allinput):
                        lookups.extend([None] * (1 + len(allinput) - len(lookups)))
                    b.addRule(
                        fontFeatures.Chaining(
                            allinput,
                            prefix,
                            suffix,
                            lookups=lookups,
                            address=self.currentLookup,
                            flags=lookup.LookupFlag,
                        )
                    )
            return
        if hasattr(sub, "BacktrackCoverage"):
            for coverage in reversed(sub.BacktrackCoverage):
                prefix.append(coverage.glyphs)
        assert not hasattr(sub, "SubstLookupRecord")
        if hasattr(sub, "InputCoverage"):
            for coverage in sub.InputCoverage:
                inputs.append(coverage.glyphs)
        if hasattr(sub, "LookAheadCoverage"):
            for i, coverage in enumerate(sub.LookAheadCoverage):
                suffix.append(coverage.glyphs)
        b.addRule(
            fontFeatures.Substitution(
                inputs,
                prefix,
                suffix,
                address=self.currentLookup,
                flags=lookup.LookupFlag,
            )
        )

    def _unparse_contextual_chain_format1(self, sub, b, lookup):
        prefix = []
        inputs = []
        lookups = []
        suffix = []
        if hasattr(sub, "ChainSubRuleSet"):
            raise ValueError
        if hasattr(sub, "BacktrackCoverage"):
            for coverage in reversed(sub.BacktrackCoverage):
                prefix.append(coverage.glyphs)
        if hasattr(sub, "SubstLookupRecord"):
            lookups = self._unparse_lookups(sub.SubstLookupRecord)
        if hasattr(sub, "InputCoverage"):
            for coverage in sub.InputCoverage:
                inputs.append(coverage.glyphs)
        if hasattr(sub, "LookAheadCoverage"):
            for i, coverage in enumerate(sub.LookAheadCoverage):
                suffix.append(coverage.glyphs)
        if len(lookups) <= len(inputs):
            lookups.extend([None] * (1 + len(inputs) - len(lookups)))
        if len(prefix) > 0 or len(suffix) > 0 or any([x is not None for x in lookups]):
            b.addRule(
                fontFeatures.Chaining(
                    inputs,
                    prefix,
                    suffix,
                    lookups=lookups,
                    address=self.currentLookup,
                    flags=lookup.LookupFlag,
                )
            )
        elif len(inputs) > 0 and (
            len(lookups) == 0 or all([x is None for x in lookups])
        ):
            # This is an Ignore
            b.addRule(
                fontFeatures.Chaining(
                    inputs,
                    prefix,
                    suffix,
                    lookups=lookups,
                    address=self.currentLookup,
                    flags=lookup.LookupFlag,
                )
            )
        else:
            # import code; code.interact(local=locals())
            b.addComment("# Another kind of contextual " + str(sub.Format))

    def _unparse_contextual_format2(self, sub, b, lookup):
        # Coverage table largely irrelevant
        # coverage = self.makeGlyphClass(sub.Coverage.glyphs)

        backtrack = {}
        if sub.BacktrackClassDef:
            backtrack = self._invertClassDef(sub.BacktrackClassDef.classDefs, self.font)
        lookahead = {}
        if sub.LookAheadClassDef:
            lookahead = self._invertClassDef(sub.LookAheadClassDef.classDefs, self.font)
        inputs = {}
        if sub.InputClassDef:
            inputs = self._invertClassDef(sub.InputClassDef.classDefs, self.font)

        rulesets = sub.ChainSubClassSet
        for classId, ruleset in enumerate(rulesets):
            if not ruleset:
                continue
            rules = ruleset.ChainSubClassRule
            inputclass = inputs[classId]
            for r in rules:
                prefix = [backtrack[x] for x in r.Backtrack]
                input_ = [inputclass] + [inputs[x] for x in r.Input]
                suffix = [lookahead[x] for x in r.LookAhead]
                lookups = self._unparse_lookups(r.SubstLookupRecord)
                if len(lookups) <= len(input_):
                    lookups.extend([None] * (1 + len(input_) - len(lookups)))
                b.addRule(
                    fontFeatures.Chaining(
                        input_,
                        prefix,
                        suffix,
                        lookups=lookups,
                        address=self.currentLookup,
                        flags=lookup.LookupFlag,
                    )
                )

    def unparseLigatureSubstitution(self, lookup):
        b = fontFeatures.Routine(
            name=self.getname("LigatureSubstitution" + self.gensym())
        )
        for sub in lookup.SubTable:
            for first, ligatures in sub.ligatures.items():
                for lig in ligatures:
                    substarray = [glyph(first)]
                    for x in lig.Component:
                        substarray.append(glyph(x))
                    b.addRule(
                        fontFeatures.Substitution(
                            substarray,
                            singleglyph(lig.LigGlyph),
                            address=self.currentLookup,
                            flags=lookup.LookupFlag,
                        )
                    )
        return b, []

    def unparseMultipleSubstitution(self, lookup):
        b = fontFeatures.Routine(
            name=self.getname("MultipleSubstitution" + self.gensym())
        )

        for sub in lookup.SubTable:
            for in_glyph, out_glyphs in sub.mapping.items():
                b.addRule(
                    fontFeatures.Substitution(
                        singleglyph(in_glyph),
                        [glyph(x) for x in out_glyphs],
                        address=self.currentLookup,
                        flags=lookup.LookupFlag,
                    )
                )
        return b, []

    def unparseAlternateSubstitution(self, lookup):
        b = fontFeatures.Routine(
            name=self.getname("AlternateSubstitution" + self.gensym())
        )
        for sub in lookup.SubTable:
            for in_glyph, out_glyphs in sub.alternates.items():
                b.addRule(
                    fontFeatures.Substitution(
                        singleglyph(in_glyph),
                        [out_glyphs],
                        address=self.currentLookup,
                        flags=lookup.LookupFlag,
                    )
                )
        return b, []

    def unparseSingleSubstitution(self, lookup):
        b = fontFeatures.Routine(
            name=self.getname("SingleSubstitution" + self.gensym())
        )
        for sub in lookup.SubTable:
            if len(sub.mapping) > 5:
                k = list(sub.mapping.keys())
                v = list(sub.mapping.values())
                b.addRule(
                    fontFeatures.Substitution(
                        [k], [v], address=self.currentLookup, flags=lookup.LookupFlag
                    )
                )
            else:
                for k, v in sub.mapping.items():
                    b.addRule(
                        fontFeatures.Substitution(
                            [[k]],
                            [[v]],
                            address=self.currentLookup,
                            flags=lookup.LookupFlag,
                        )
                    )
        return b, []

    def getDependencies(self, lookup):
        deps = []
        if lookup.LookupType == 7:
            for xt in lookup.SubTable:
                subLookupType = xt.ExtSubTable.LookupType
                if self.isChaining(subLookupType):
                    deps.extend(self.getDependencies(xt.ExtSubTable))
                else:
                    return []

        elif hasattr(lookup, "SubTable"):
            for sub in lookup.SubTable:
                deps.extend(self.getChainingDeps(sub))
        else:
            deps.extend(self.getChainingDeps(lookup))
        return set(deps)

    def getChainingDeps(self, sub):
        deps = []
        if hasattr(sub, "ChainSubClassSet") or hasattr(sub, "SubClassSet"):
            rulesets = (
                hasattr(sub, "ChainSubClassSet")
                and sub.ChainSubClassSet
                or sub.SubClassSet
            )
            for classId, ruleset in enumerate(rulesets):
                if not ruleset:
                    continue
                if hasattr(ruleset, "ChainSubClassRule"):
                    rules = ruleset.ChainSubClassRule
                else:
                    rules = ruleset.SubClassRule
                for r in rules:
                    for sl in r.SubstLookupRecord:
                        deps.append(sl.LookupListIndex)
        elif hasattr(sub, "SubRuleSet"):
            for subrulesets, input_ in zip(sub.SubRuleSet, sub.Coverage.glyphs):
                for subrule in subrulesets.SubRule:
                    for sl in subrule.SubstLookupRecord:
                        deps.append(sl.LookupListIndex)

        elif hasattr(sub, "SubstLookupRecord"):
            for sl in sub.SubstLookupRecord:
                deps.append(sl.LookupListIndex)
        return deps
