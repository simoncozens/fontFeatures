from fontTools.misc.py23 import *
import fontTools
from fontTools.feaLib.ast import *
from collections import OrderedDict
from .GTableUnparser import GTableUnparser
from itertools import groupby
from fontTools.misc.xmlWriter import XMLWriter

def _invertClassDef(a):
    return {k: [j for j, _ in list(v)] for k, v in groupby(a.items(), lambda x: x[1])}

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

    def unparseExtension(self, lookup):
        for xt in lookup.SubTable:
            xt.SubTable = [ xt.ExtSubTable ]
            xt.LookupType = xt.ExtSubTable.LookupType
            return self.unparseLookup(xt)

    def unparseContextualSubstitution(self,lookup):
        b = LookupBlock(name='ContextualSubstitution'+self.gensym())

        b.statements.append( Comment("# A contextual subst goes here") )
        return b, []

    def unparseChainingContextualSubstitution(self,lookup):
        b = LookupBlock(name='ChainingContextualSubstitution'+self.gensym())
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
                prefix.append(self.makeGlyphClass( coverage.glyphs ))
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
                inputs.append(self.makeGlyphClass(coverage.glyphs))
        if hasattr(sub, "LookAheadCoverage"):
            for i, coverage in enumerate(sub.LookAheadCoverage):
                suffix.append(self.makeGlyphClass(coverage.glyphs))
        if len(lookups) <= len(inputs):
            lookups.extend([None] * (1+len(inputs)-len(lookups)))
        if len(prefix) > 0 or len(suffix)>0 or any([x is not None for x in lookups]):
            b.statements.append(ChainContextSubstStatement(prefix,inputs,suffix,lookups))
        elif len(inputs) > 0 and (len(lookups) == 0 or all([x is None for x in lookups])):
            b.statements.append(IgnoreSubstStatement([(prefix,inputs,suffix)]))
        else:
            b.statements.append(Comment("# Another kind of contextual "+str(sub.Format)))

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
                inputclass = self.makeGlyphClass(inputs[classId])
                for r in rules:
                    prefix = [ self.makeGlyphClass(backtrack[x]) for x in r.Backtrack ]
                    input_ = [inputclass] + [ self.makeGlyphClass(inputs[x]) for x in r.Input ]
                    suffix = [ self.makeGlyphClass(lookahead[x]) for x in r.LookAhead ]
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
                    b.statements.append(ChainContextSubstStatement(prefix,input_,suffix,lookups))
        except Exception as e:
            writer = XMLWriter(BytesIO())
            b.statements.append(Comment("# XXX Unparsable rule: "+str(e)))
            sub.toXML(writer, self.font)
            b.statements.append(Comment(writer.file.getvalue().decode("utf-8")))

    def unparseLigatureSubstitution(self,lookup):
        b = LookupBlock(name='LigatureSubstitution'+self.gensym())
        # XXX Lookup flag

        for sub in lookup.SubTable:
            for first, ligatures in sub.ligatures.items():
                for lig in ligatures:
                    substarray =  [GlyphName(first)]
                    for x in lig.Component:
                        substarray.append(GlyphName(x))
                    b.statements.append(LigatureSubstStatement(
                        [],
                        substarray,
                        [],
                        GlyphName(lig.LigGlyph),False))
        return b, []

    def unparseMultipleSubstitution(self,lookup):
        b = LookupBlock(name='MultipleSubstitution'+self.gensym())

        for sub in lookup.SubTable:
            for in_glyph, out_glyphs in sub.mapping.items():
                out_array =  [GlyphName(x) for x in out_glyphs]
                b.statements.append(MultipleSubstStatement(
                    [],
                    GlyphName(in_glyph),
                    [],
                    out_glyphs,False))
        return b, []

    def unparseAlternateSubstitution(self,lookup):
        b = LookupBlock(name='AlternateSubstitution'+self.gensym())
        for sub in lookup.SubTable:
            for in_glyph, out_glyphs in sub.alternates.items():
                b.statements.append(AlternateSubstStatement(
                    [],
                    GlyphName(in_glyph),
                    [],
                    self.makeGlyphClass(out_glyphs),False))
        return b, []

    def unparseSingleSubstitution(self,lookup):
        b = LookupBlock(name='SingleSubstitution'+self.gensym())
        # XXX Lookup flag

        for sub in lookup.SubTable:
            if len(sub.mapping) > 5:
                k = self.makeGlyphClass(sub.mapping.keys())
                v = self.makeGlyphClass(sub.mapping.values())
                b.statements.append(SingleSubstStatement([k],[v],[],[],False))
            else:
                for k,v in sub.mapping.items():
                    b.statements.append(SingleSubstStatement([GlyphName(k)],[GlyphName(v)],[],[],False))
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
                for sl in sub.SubstLookupRecord:
                    deps.append(sl.LookupListIndex)
        return set(deps)