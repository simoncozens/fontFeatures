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
    _table = "GSUB"
    lookupTypes = {
        1: "SingleSubstitution",
        2: "MultipleSubstitution",
        3: "AlternateSubstitution",
        4: "LigatureSubstitution",
        5: "Contextual",
        6: "ChainedContextual",
        7: "Extension",
        8: "ReverseContextualSubstitution",
    }

    _attrs = {
        "lookup": "SubstLookupRecord",
        "format1_ruleset": "SubRuleSet",
        "format1_rule": "SubRule",
        "format2_classset": "SubClassSet",
        "format2_rule": "SubClassRule",
        "chain_format1_ruleset": "ChainSubRuleSet",
        "chain_format1_rule": "ChainSubRule",
        "chain_format2_classset": "ChainSubClassSet",
        "chain_format2_rule": "ChainSubClassRule",
    }

    def isChaining(self, lookupType):
        return lookupType >= 5

    def unparseReverseContextualSubstitution(self, lookup):
        b = fontFeatures.Routine(
            name=self.getname("ReverseContextualSubstitution" + self.gensym())
        )
        self._fix_flags(b, lookup)
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

    def unparseLigatureSubstitution(self, lookup):
        b = fontFeatures.Routine(
            name=self.getname("LigatureSubstitution" + self.gensym())
        )
        self._fix_flags(b, lookup)
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
        self._fix_flags(b, lookup)

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
        self._fix_flags(b, lookup)
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
        self._fix_flags(b, lookup)
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
