from fontTools.misc.py23 import *
import fontTools
from fontTools.feaLib.ast import *
from collections import OrderedDict
from .GTableUnparser import GTableUnparser

class GSUBUnparser (GTableUnparser):
    lookupTypes = {
        1: "SingleSubstitution",
        2: "MultipleSubstitution",
        3: "AlternateSubstitution",
        4: "LigatureSubstitution",
        5: "ChainingContextualSubstitution",
        6: "ChainingContextualSubstitution",
        7: "Extension",
        8: "NotImplemented8GSUB",
    }

    def unparseExtension(self, lookup):
        for xt in lookup.SubTable:
            xt.SubTable = [ xt.ExtSubTable ]
            xt.LookupType = xt.ExtSubTable.LookupType
            return self.unparseLookup(xt)

    def unparseChainingContextualSubstitution(self,lookup):
        b = LookupBlock(name='ChainingContextualSubstitution'+self.gensym())
        for sub in lookup.SubTable:
            prefix = []
            inputs = []
            lookups = []
            suffix = []
            if hasattr(sub, "BacktrackCoverage"):
                for coverage in reversed(sub.BacktrackCoverage):
                    prefix.append(GlyphClass([ GlyphName(c) for c in coverage.glyphs ]))
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
                    inputs.append(GlyphClass([ GlyphName(c) for c in coverage.glyphs ]))
            if hasattr(sub, "LookAheadCoverage"):
                for i, coverage in enumerate(sub.LookAheadCoverage):
                    suffix.append(GlyphClass([ GlyphName(c) for c in coverage.glyphs ]))
            if len(lookups) <= len(inputs):
                lookups.extend([None] * (1+len(inputs)-len(lookups)))
            if len(prefix) > 0 or len(suffix)>0:
                b.statements.append(ChainContextSubstStatement(prefix,inputs,suffix,lookups))
            else:
                b.statements.append(Comment("# Another kind of contextual XXX"))
        return b, []

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
                out_array =  [GlyphName(x) for x in out_glyphs]
                b.statements.append(AlternateSubstStatement(
                    [],
                    GlyphName(in_glyph),
                    [],
                    GlyphClass(out_glyphs),False))
        return b, []

    def unparseSingleSubstitution(self,lookup):
        b = LookupBlock(name='SingleSubstitution'+self.gensym())
        # XXX Lookup flag

        for sub in lookup.SubTable:
            for k,v in sub.mapping.items():
                b.statements.append(SingleSubstStatement([GlyphName(k)],[GlyphName(v)],[],[],False))
        return b, []
