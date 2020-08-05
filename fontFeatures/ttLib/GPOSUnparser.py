from .GTableUnparser import GTableUnparser
import fontFeatures


class GPOSUnparser(GTableUnparser):
    lookupTypes = {
        1: "SinglePositioning",
        2: "PairPositioning",
        3: "CursiveAttachment",
        4: "MarkToBase",
        5: "MarkToLigature",
        6: "MarkToMark",
        7: "ContextualPositioning",
        8: "ChainedContextualPositioning",
        9: "Extension",
    }

    def makeValueRecord(self, valueRecord, valueFormat):
        valueFormatFlags = (
            ("XPlacement", 0x0001),  # Includes horizontal adjustment for placement
            ("YPlacement", 0x0002),  # Includes vertical adjustment for placement
            ("XAdvance", 0x0004),  # Includes horizontal adjustment for advance
            ("YAdvance", 0x0008),  # Includes vertical adjustment for advance
            ("XPlaDevice", 0x0010),  # Includes horizontal Device table for placement
            ("YPlaDevice", 0x0020),  # Includes vertical Device table for placement
            ("XAdvDevice", 0x0040),  # Includes horizontal Device table for advance
            ("YAdvDevice", 0x0080)  # Includes vertical Device table for advance
            # , 'Reserved': 0xF000 For future use (set to zero)
        )

        # defaults to 0
        # NOTE: this is likely not correct anymore when we start doing the
        # <device> tables in Value record format C.
        values = [getattr(valueRecord, name, 0) or None for name, _ in valueFormatFlags]
        return fontFeatures.ValueRecord(*values)

    def isChaining(self, lookupType):
        return lookupType >= 7

    def getDependencies(self, lookup):
        deps = []
        if lookup.LookupType == 9:
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
        if hasattr(sub, "ChainPosClassSet") or hasattr(sub, "PosClassSet"):
            rulesets = (
                hasattr(sub, "ChainPosClassSet")
                and sub.ChainPosClassSet
                or sub.PosClassSet
            )
            for classId, ruleset in enumerate(rulesets):
                if not ruleset:
                    continue
                if hasattr(ruleset, "ChainPosClassRule"):
                    rules = ruleset.ChainPosClassRule
                else:
                    rules = ruleset.PosClassRule
                for r in rules:
                    for sl in r.PosLookupRecord:
                        deps.append(sl.LookupListIndex)
        elif hasattr(sub, "PosRuleSet"):
            for subrulesets, input_ in zip(sub.PosRuleSet, sub.Coverage.glyphs):
                for subrule in subrulesets.PosRule:
                    for sl in subrule.PosLookupRecord:
                        deps.append(sl.LookupListIndex)

        elif hasattr(sub, "PosLookupRecord"):
            for sl in sub.PosLookupRecord:
                deps.append(sl.LookupListIndex)
        return deps

    def unparseSinglePositioning(self, lookup):
        b = fontFeatures.Routine(name=self.getname("SinglePositioning" + self.gensym()))

        for subtable in lookup.SubTable:
            if subtable.Format == 1:
                spos = fontFeatures.Positioning(
                    [subtable.Coverage.glyphs],
                    [self.makeValueRecord(subtable.Value, subtable.ValueFormat)],
                )
                b.addRule(spos)
            else:
                # Optimize it later
                for g, v in zip(subtable.Coverage.glyphs, subtable.Value):
                    spos = fontFeatures.Positioning(
                        [[g]], [self.makeValueRecord(v, subtable.ValueFormat)]
                    )
                    b.addRule(spos)
        return b, []

    def unparsePairPositioning(self, lookup):
        b = fontFeatures.Routine(name=self.getname("PairPositioning" + self.gensym()))
        for subtable in lookup.SubTable:
            if subtable.Format == 1:
                for g, pair in zip(subtable.Coverage.glyphs, subtable.PairSet):
                    for vr in pair.PairValueRecord:
                        spos = fontFeatures.Positioning(
                            [[g], [vr.SecondGlyph]],
                            [
                                self.makeValueRecord(vr.Value1, subtable.ValueFormat1),
                                self.makeValueRecord(vr.Value2, subtable.ValueFormat2),
                            ],
                        )
                        b.addRule(spos)
            else:
                class1 = self._invertClassDef(subtable.ClassDef1.classDefs, self.font)
                class2 = self._invertClassDef(subtable.ClassDef2.classDefs, self.font)
                for ix1, c1 in enumerate(subtable.Class1Record):
                    if ix1 not in class1:
                        continue  # XXX
                    for ix2, c2 in enumerate(c1.Class2Record):
                        if ix2 not in class2:
                            continue  # XXX
                        vr1 = self.makeValueRecord(c2.Value1, subtable.ValueFormat1)
                        vr2 = self.makeValueRecord(c2.Value2, subtable.ValueFormat2)
                        if not vr1 and not vr2:
                            continue
                        firstClass = list(
                            set(class1[ix1]) & set(subtable.Coverage.glyphs)
                        )
                        spos = fontFeatures.Positioning(
                            [firstClass, class2[ix2]], [vr1, vr2]
                        )
                        b.addRule(spos)
        return b, []

    def unparseCursiveAttachment(self, lookup):
        b = fontFeatures.Routine(name=self.getname("CursiveAttachment" + self.gensym()))
        entries = {}
        exits = {}
        for s in lookup.SubTable:
            assert s.Format == 1
            for glyph, record in zip(s.Coverage.glyphs, s.EntryExitRecord):
                if record.EntryAnchor:
                    entries[glyph] = (
                        record.EntryAnchor.XCoordinate,
                        record.EntryAnchor.YCoordinate,
                    )
                if record.ExitAnchor:
                    exits[glyph] = (
                        record.ExitAnchor.XCoordinate,
                        record.ExitAnchor.YCoordinate,
                    )
        b.addRule(
            fontFeatures.Attachment(
                "cursive_entry", "cursive_exit", entries, exits, flags=lookup.LookupFlag
            )
        )
        return b, []

    def unparseMarkToBase(self, lookup):
        b = fontFeatures.Routine(name=self.getname("MarkToBase" + self.gensym()))
        for subtable in lookup.SubTable:  # fontTools.ttLib.tables.otTables.MarkBasePos
            assert subtable.Format == 1
            for classId in range(0,subtable.ClassCount):
                anchorClassPrefix = "Anchor" + self.gensym()
                marks = self.formatMarkArray(
                    subtable.MarkArray, subtable.MarkCoverage, classId
                )
                bases = self.formatBaseArray(
                    subtable.BaseArray, subtable.BaseCoverage, classId
                )
                b.addRule(
                    fontFeatures.Attachment(
                        anchorClassPrefix, anchorClassPrefix + "_", bases, marks,
                        font = self.font
                    )
                )
        return b, []

    def formatMarkArray(self, markArray, markCoverage, classId):
        id2Name = markCoverage.glyphs
        marks = {}
        for i, markRecord in enumerate(markArray.MarkRecord):
            if markRecord.Class == classId:
                marks[id2Name[i]] = (
                    markRecord.MarkAnchor.XCoordinate,
                    markRecord.MarkAnchor.YCoordinate,
                    markRecord.Class
                )
        return marks

    def formatMark2Array(self, markArray, markCoverage, anchorClassPrefix):
        id2Name = markCoverage.glyphs
        marks = {}
        for i, markRecord in enumerate(markArray.Mark2Record):
            assert len(markRecord.Mark2Anchor) == 1
            marks[id2Name[i]] = (
                markRecord.Mark2Anchor[0].XCoordinate,
                markRecord.Mark2Anchor[0].YCoordinate,
            )
        return marks

    def formatBaseArray(self, baseArray, baseCoverage, wantedClassId):
        id2Name = baseCoverage.glyphs
        bases = {}
        for i, baseRecord in enumerate(baseArray.BaseRecord):
            for classId, anchor in enumerate(baseRecord.BaseAnchor):
                if classId != wantedClassId:
                    continue
                if not anchor:
                    continue
                bases[id2Name[i]] = (anchor.XCoordinate, anchor.YCoordinate)  # ClassId?
        return bases

    def unparseMarkToLigature(self, lookup):
        b = fontFeatures.Routine(name=self.getname("MarkToLigature" + self.gensym()))
        self.unparsable(b, "Mark to lig pos", lookup)
        return b, []

    def unparseMarkToMark(self, lookup):
        b = fontFeatures.Routine(name=self.getname("MarkToMark" + self.gensym()))
        for subtable in lookup.SubTable:  # fontTools.ttLib.tables.otTables.MarkBasePos
            assert subtable.Format == 1
            anchorClassPrefix = "Anchor" + self.gensym()
            marks = self.formatMarkArray(
                subtable.Mark1Array, subtable.Mark1Coverage, anchorClassPrefix
            )
            bases = self.formatMark2Array(
                subtable.Mark2Array, subtable.Mark2Coverage, anchorClassPrefix
            )
            b.addRule(
                fontFeatures.Attachment(
                    anchorClassPrefix, anchorClassPrefix + "_", bases, marks,
                    font = self.font
                )
            )
        return b, []

    def unparseContextualPositioning(self, lookup):
        b = fontFeatures.Routine(
            name=self.getname("ContextualPositioning" + self.gensym())
        )
        for sub in lookup.SubTable:
            if sub.Format == 1:
                self._unparse_contextual_pos_format1(sub, b, lookup)
            else:
                try:
                    inputs = self._invertClassDef(sub.ClassDef.classDefs, self.font)
                    for classId, ruleset in enumerate(sub.PosClassSet):
                        if not ruleset:
                            continue
                        rules = ruleset.PosClassRule
                        inputclass = inputs[classId]
                        for r in rules:
                            input_ = [inputclass] + [inputs[x] for x in r.Class]
                            lookups = self._unparse_lookups(r.PosLookupRecord)
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

    def _unparse_contextual_pos_format1(self, sub, b, lookup):
        prefix = []
        inputs = []
        lookups = []
        suffix = []
        if hasattr(sub, "PosRuleSet"):
            for subrulesets, input_ in zip(sub.PosRuleSet, sub.Coverage.glyphs):
                for subrule in subrulesets.PosRule:
                    lookups = self._unparse_lookups(subrule.PosLookupRecord, lookups)
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
            return
        if hasattr(sub, "BacktrackCoverage"):
            for coverage in reversed(sub.BacktrackCoverage):
                prefix.append(coverage.glyphs)
        if hasattr(sub, "PosLookupRecord"):
            lookups = self._unparse_lookups(subrule.PosLookupRecord, lookups)
        if hasattr(sub, "InputCoverage"):
            for coverage in sub.InputCoverage:
                inputs.append(coverage.glyphs)
        if hasattr(sub, "LookAheadCoverage"):
            for i, coverage in enumerate(sub.LookAheadCoverage):
                suffix.append(coverage.glyphs)
        b.addRule(
            fontFeatures.Positioning(
                inputs,
                prefix,
                suffix,
                address=self.currentLookup,
                flags=lookup.LookupFlag,
            )
        )

    def unparseChainedContextualPositioning(self, lookup):
        b = fontFeatures.Routine(
            name=self.getname("ChainedContextualPositioning" + self.gensym())
        )
        self.unparsable(b, "Chained Contextual pos", lookup)
        return b, []
