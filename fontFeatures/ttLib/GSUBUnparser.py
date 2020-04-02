from fontTools.misc.py23 import *
import fontTools
from collections import OrderedDict
from .GTableUnparser import GTableUnparser
from itertools import groupby
import fontFeatures

def _invertClassDef(a):
    return {k: [j for j, _ in list(v)] for k, v in groupby(a.items(), lambda x: x[1])}

# These are silly little functions which help to document the intent

def glyph(x):
    assert(isinstance(x, str))
    return [x]

def singleglyph(x):
    return [glyph(x)]

class GSUBUnparser (GTableUnparser):
    lookupTypes = {
        1: "SingleSubstitution",
        2: "MultipleSubstitution",
        3: "AlternateSubstitution",
        4: "LigatureSubstitution",
        5: "ContextualSubstitution",
        6: "ChainingContextualSubstitution",
        7: "Extension",
        8: "NotImplemented8GSUB",
    }

    def isChaining(self, lookupType):
        return lookupType >= 6

    def unparseContextualSubstitution(self,lookup):
        b = fontFeatures.Routine(name='ContextualSubstitution'+self.gensym())

        b.addComment("A contextual subst goes here")
        for sub in lookup.SubTable:
            if sub.Format == 1:
                self._unparse_contextual_format1(sub, b)
            else:
                self.unparsable(b, "Lookup type 5", sub)

        return b, []

    def unparseChainingContextualSubstitution(self,lookup):
        b = fontFeatures.Routine(name='ChainingContextualSubstitution'+self.gensym())
        for sub in lookup.SubTable:
            if sub.Format == 1 or sub.Format == 3:
                self._unparse_contextual_format1(sub, b)
            elif sub.Format == 2:
                self._unparse_contextual_format2(sub, b)
            else:
                raise ValueError
        return b, []

    def _unparse_contextual_format1(self, sub, b):
        prefix = []
        inputs = []
        lookups = []
        suffix = []
        if hasattr(sub, "BacktrackCoverage"):
            for coverage in reversed(sub.BacktrackCoverage):
                prefix.append( coverage.glyphs )
        if hasattr(sub, "SubstLookupRecord"):
            for sl in sub.SubstLookupRecord:
                self.lookups[sl.LookupListIndex]["inline"] = False
                self.lookups[sl.LookupListIndex]["useCount"] = 999
                self.sharedLookups.add(sl.LookupListIndex)
                if len(lookups) <= sl.SequenceIndex:
                    lookups.extend([None] * (1+sl.SequenceIndex-len(lookups)))

                lookups[sl.SequenceIndex] = self.lookups[sl.LookupListIndex]["lookup"]
        if hasattr(sub, "InputCoverage"):
            for coverage in sub.InputCoverage:
                inputs.append(coverage.glyphs)
        if hasattr(sub, "LookAheadCoverage"):
            for i, coverage in enumerate(sub.LookAheadCoverage):
                suffix.append(coverage.glyphs)
        if len(lookups) <= len(inputs):
            lookups.extend([None] * (1+len(inputs)-len(lookups)))
        if len(prefix) > 0 or len(suffix)>0 or any([x is not None for x in lookups]):
            b.addRule(fontFeatures.Chaining(inputs,prefix,suffix,lookups = lookups))
        elif len(inputs) > 0 and (len(lookups) == 0 or all([x is None for x in lookups])):
            # This is an Ignore
            b.addRule(fontFeatures.Chaining(inputs,prefix,suffix,lookups = lookups))
        else:
            b.addComment("# Another kind of contextual "+str(sub.Format))

    def _unparse_contextual_format2(self, sub, b):
        # Coverage table largely irrelevant
        # coverage = self.makeGlyphClass(sub.Coverage.glyphs)
        backtrack = {}
        if hasattr(sub, "BacktrackClassDef") and sub.BacktrackClassDef:
            backtrack = _invertClassDef(sub.BacktrackClassDef.classDefs)
        lookahead = {}
        if hasattr(sub, "LookAheadClassDef") and sub.LookAheadClassDef:
            lookahead = _invertClassDef(sub.LookAheadClassDef.classDefs)
        inputs = {}
        if hasattr(sub, "InputClassDef") and sub.InputClassDef:
            inputs = _invertClassDef(sub.InputClassDef.classDefs)

        rulesets = hasattr(sub, "ChainSubClassSet") and sub.ChainSubClassSet or sub.SubClassSet

        try:
            for classId, ruleset in enumerate(rulesets):
                if not ruleset: continue
                rules = hasattr(ruleset, "ChainSubClassRule") and ruleset.ChainSubClassRule or ruleset.SubClassRule
                inputclass = inputs[classId]
                for r in rules:
                    prefix = [ backtrack[x] for x in r.Backtrack ]
                    input_ = [ inputclass ] + [ inputs[x] for x in r.Input ]
                    suffix = [ lookahead[x] for x in r.LookAhead ]
                    lookups = []
                    for sl in r.SubstLookupRecord:
                        self.lookups[sl.LookupListIndex]["inline"] = False
                        self.lookups[sl.LookupListIndex]["useCount"] = 999
                        self.sharedLookups.add(sl.LookupListIndex)
                        if len(lookups) <= sl.SequenceIndex:
                            lookups.extend([None] * (1+sl.SequenceIndex-len(lookups)))
                        lookups[sl.SequenceIndex] = self.lookups[sl.LookupListIndex]["lookup"]
                    if len(lookups) <= len(input_):
                        lookups.extend([None] * (1+len(input_)-len(lookups)))
                    b.addRule(fontFeatures.Chaining(input_,input_,prefix,suffix,lookups=lookups))
        except Exception as e:
            self.unparsable(b, e, sub)

    def unparseLigatureSubstitution(self,lookup):
        b = fontFeatures.Routine(name='LigatureSubstitution'+self.gensym())
        # XXX Lookup flag

        for sub in lookup.SubTable:
            for first, ligatures in sub.ligatures.items():
                for lig in ligatures:
                    substarray = [glyph(first)]
                    for x in lig.Component:
                        substarray.append(glyph(x))
                    b.addRule(fontFeatures.Substitution(substarray, singleglyph(lig.LigGlyph)))
        return b, []

    def unparseMultipleSubstitution(self,lookup):
        b = fontFeatures.Routine(name='MultipleSubstitution'+self.gensym())

        for sub in lookup.SubTable:
            for in_glyph, out_glyphs in sub.mapping.items():
                b.addRule(fontFeatures.Substitution(singleglyph(in_glyph), [glyph(x) for x in out_glyphs]))
        return b, []

    def unparseAlternateSubstitution(self,lookup):
        b = fontFeatures.Routine(name='AlternateSubstitution'+self.gensym())
        for sub in lookup.SubTable:
            for in_glyph, out_glyphs in sub.alternates.items():
                b.addRule(fontFeatures.Substitution(singleglyph(in_glyph), [out_glyphs]))
        return b, []

    def unparseSingleSubstitution(self,lookup):
        b = fontFeatures.Routine(name='SingleSubstitution'+self.gensym())
        # XXX Lookup flag

        for sub in lookup.SubTable:
            if len(sub.mapping) > 5:
                k =sub.mapping.keys()
                v =sub.mapping.values()
                b.addRule(fontFeatures.Substitution([k],[v]))
            else:
                for k,v in sub.mapping.items():
                    b.addRule(fontFeatures.Substitution([[k]],[[v]]))
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

        elif hasattr(lookup,"ChainSubClassSet"): # Format 2
            for ruleset in lookup.ChainSubClassSet:
                if ruleset is None: continue
                for rule in ruleset.ChainSubClassRule:
                    for sl in rule.SubstLookupRecord:
                        deps.append(sl.LookupListIndex)
        else:
            for sub in lookup.SubTable:
                if hasattr(sub, "SubstLookupRecord"):
                    for sl in sub.SubstLookupRecord:
                        deps.append(sl.LookupListIndex)
        return set(deps)
