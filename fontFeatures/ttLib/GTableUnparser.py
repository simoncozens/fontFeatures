from collections import OrderedDict
from fontTools.misc.xmlWriter import XMLWriter
import fontFeatures
from io import BytesIO


class GTableUnparser:
    def __init__(self, table, ff, languageSystems, font=None, config={}):
        self.table = table.table
        self.font = font
        self.fontFeatures = ff
        self.lookupNames = []
        self.config = config
        self.index = 0
        self.lookups = {}
        self.sharedClasses = {}
        self.languageSystems = languageSystems
        self.sharedLookups = OrderedDict()

    def _unparse_lookups(self, slr, in_lookups=None):
        lookups = []
        if in_lookups:
            lookups = in_lookups
        for sl in slr:
            self.lookups[sl.LookupListIndex]["inline"] = False
            self.lookups[sl.LookupListIndex]["useCount"] = 999
            self.sharedLookups[sl.LookupListIndex] = None
            if len(lookups) <= sl.SequenceIndex:
                lookups.extend([None] * (1 + sl.SequenceIndex - len(lookups)))
            if not lookups[sl.SequenceIndex]:
                lookups[sl.SequenceIndex] = []
            lookups[sl.SequenceIndex].append(self.lookups[sl.LookupListIndex]["lookup"])
        return lookups

    def _invertClassDef(self, a, font):
        classes = {}
        for glyph, klass in a.items():
            if klass not in classes:
                classes[klass] = []
            classes[klass].append(glyph)
        glyphset = set(font.getGlyphOrder())
        classes[0] = glyphset - set(a.keys())
        return classes

    def getname(self, n):
        if n in self.config:
            return self.config[n]
        return n

    def gensym(self):
        self.index = self.index + 1
        return str(self.index)

    def unparse(self, doLookups=True):
        if doLookups:
            self.unparseLookups()
        self.collectFeatures()
        self.tidyFeatures()
        if doLookups:
            self.inlineFeatures()
            # self.addGlyphClasses()
        self.addFeatures(doLookups=doLookups)

    # def addGlyphClasses(self):
    #     self.feature.statements.append(Comment('\n# Glyph classes\n'))
    #     for gc in self.sharedClasses.values():
    #         self.feature.statements.append(gc)

    def _prepareFeatureLangSys(self, langTag, langSys, table, features, scriptTag):
        # This is a part of prepareFeatures
        for featureIdx in langSys.FeatureIndex:
            featureRecord = self.table.FeatureList.FeatureRecord[featureIdx]
            featureTag = featureRecord.FeatureTag
            scripts = features.get(featureTag, None)
            if scripts is None:
                scripts = OrderedDict()
                features[featureTag] = scripts

            languages = scripts.get(scriptTag, None)
            if languages is None:
                languages = OrderedDict()
                scripts[scriptTag] = languages

            lookups = languages.get(langTag, None)
            if lookups is None:
                lookups = []
                languages[langTag] = lookups

            for lookupIdx in featureRecord.Feature.LookupListIndex:
                lookups.append(lookupIdx)

    def collectFeatures(self):
        features = OrderedDict()
        for scriptRecord in self.table.ScriptList.ScriptRecord:
            scriptTag = scriptRecord.ScriptTag
            if scriptRecord.Script.DefaultLangSys is not None:
                self._prepareFeatureLangSys(
                    "dflt",
                    scriptRecord.Script.DefaultLangSys,
                    self.table,
                    features,
                    scriptTag,
                )
            for langSysRecord in scriptRecord.Script.LangSysRecord:
                self._prepareFeatureLangSys(
                    langSysRecord.LangSysTag,
                    langSysRecord.LangSys,
                    self.table,
                    features,
                    scriptTag,
                )
        self.features = features

    def tidyFeatures(self):
        # Now tidy up. Most common case is a set of lookups duplicated to all language systems
        for name, feature in self.features.items():
            # print(feature["DFLT"]["dflt"])
            allLookups = [
                langLookup
                for script in feature.values()
                for langLookup in script.values()
            ]
            lookupsAreEqual = [x == allLookups[0] for x in allLookups]
            if all(lookupsAreEqual):
                self.features[name] = {"DFLT": {"dflt": allLookups[0]}}

        # Also check for individual lookups which can be hoisted to default
        for name, feature in self.features.items():
            allLookups = [
                langLookup
                for script in feature.values()
                for langLookup in script.values()
            ]
            for lookupIx in allLookups[0]:
                everyoneGetsIt = all([lookupIx in x for x in allLookups])
                if everyoneGetsIt and len(allLookups) > 1:
                    for arr in allLookups[1:]:
                        arr.remove(lookupIx)

    def inlineFeatures(self):
        # Check which can be inlined and which are shared
        for name, feature in self.features.items():
            for script in feature.values():
                for langLookups in script.values():
                    for lookupIdx in langLookups:
                        self.lookups[lookupIdx]["useCount"] = (
                            self.lookups[lookupIdx]["useCount"] + 1
                        )
                        if (
                            self.lookups[lookupIdx]["useCount"] > 1
                            and len(self.lookups[lookupIdx]["lookup"].rules) > 3
                        ):
                            for l in self.lookups[lookupIdx]["dependencies"]:
                                self.markAsSharedAndAdd(l)
                            self.markAsSharedAndAdd(lookupIdx)

    def markAsSharedAndAdd(self, lookupIdx):
        self.lookups[lookupIdx]["inline"] = False
        self.sharedLookups[lookupIdx] = None

    def addFeatures(self, doLookups=True):
        if doLookups:
            for l in self.sharedLookups.keys():
                self.fontFeatures.addRoutine(self.lookups[l]["lookup"])

        for name, feature in self.features.items():
            f = []
            for scriptname, langs in feature.items():
                for lang, lookups in langs.items():
                    if doLookups:
                        for lookupIdx in lookups:
                            routine = self.lookups[lookupIdx]["lookup"]
                            if not (scriptname == "DFLT" and lang == "dflt"):
                                self.lookups[lookupIdx]["inline"] = True
                            if self.lookups[lookupIdx]["inline"]:
                                newroutine = fontFeatures.Routine(
                                    languages=[(scriptname, lang)],
                                    address = routine.address,
                                    flags = routine.flags,
                                    name = routine.name
                                )
                                newroutine.rules.extend(routine.rules)
                                f.append(newroutine)
                            else:
                                f.append(routine)
            self.fontFeatures.addFeature(name, f)

    def unparseLookups(self):
        lookupOrder = range(0, len(self.table.LookupList.Lookup))
        # Reorder to check for dependencies
        newOrder = []
        while True:
            changed = False
            newOrder = []
            for lookupIdx in lookupOrder:
                lookup = self.table.LookupList.Lookup[lookupIdx]
                if self.isChaining(lookup.LookupType):
                    dependencies = self.getDependencies(lookup)
                    for l in dependencies:
                        if l not in newOrder:
                            newOrder.append(l)
                            changed = True
                if lookupIdx not in newOrder:
                    newOrder.append(lookupIdx)
            lookupOrder = newOrder
            if not changed:
                break

        for lookupIdx in lookupOrder:
            lookup = self.table.LookupList.Lookup[lookupIdx]
            res, dependencies = self.unparseLookup(lookup, lookupIdx)
            res.address = (self._table, lookupIdx)
            debug = self.getDebugInfo(self._table, lookupIdx)
            if debug:
                res.address = (self._table, lookupIdx, *debug)
                if debug[1]:
                    res.name = debug[1]
            self.lookups[lookupIdx] = {
                "lookup": res,
                "dependencies": dependencies,
                "useCount": 0,
                "inline": True,
            }

    def unparseLookup(self, lookup, lookupIdx):
        self.currentLookup = lookupIdx
        unparser = getattr(self, "unparse" + self.lookupTypes[lookup.LookupType])
        return unparser(lookup)

    def unparseExtension(self, lookup):
        for xt in lookup.SubTable:
            xt.SubTable = [xt.ExtSubTable]
            xt.LookupType = xt.ExtSubTable.LookupType
            xt.LookupFlag = lookup.LookupFlag
            return self.unparseLookup(xt, self.currentLookup)

    def getDebugInfo(self, table, ix):
        if not self.font or 'Debg' not in self.font:
            return None
        debug_data = self.font["Debg"].data
        if 'com.github.fonttools.feaLib' not in debug_data:
            return None
        debug_data = debug_data['com.github.fonttools.feaLib'][table][str(ix)]
        return debug_data[0], debug_data[1]

    def asXML(self, sub):
        writer = XMLWriter(BytesIO())
        sub.toXML(writer, self.font)
        out = writer.file.getvalue().decode("utf-8")
        return out

    def unparsable(self, b, e, sub):
        import warnings

        warnings.warn(
            "# XXX Unparsable rule: " + str(e) + " in " + str(self.currentLookup)
        )
        b.addComment("# ----")
        out = self.asXML(sub).splitlines()
        for ln in out:
            b.addComment("# " + ln)
        b.addComment("# ----\n")


    def _unparse_contextual_chain_format1(self, sub, b, lookup):
        prefix = []
        inputs = []
        lookups = []
        suffix = []
        if hasattr(sub, "BacktrackCoverage"):
            for coverage in reversed(sub.BacktrackCoverage):
                prefix.append(coverage.glyphs)

        if hasattr(sub, "SubstLookupRecord"):
            lookups = self._unparse_lookups(sub.SubstLookupRecord)
        elif hasattr(sub, "PosLookupRecord"):
            lookups = self._unparse_lookups(sub.PosLookupRecord)

        if hasattr(sub, "InputCoverage"):
            for coverage in sub.InputCoverage:
                inputs.append(coverage.glyphs)
        if hasattr(sub, "LookAheadCoverage"):
            for i, coverage in enumerate(sub.LookAheadCoverage):
                suffix.append(coverage.glyphs)
        if len(lookups) < len(inputs):
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
        rulesetattr, ruleattr, lookupattr = [self._format2_attrs[x] for x in ["ruleset", "rule", "lookup"]]

        backtrack = {}
        if sub.BacktrackClassDef:
            backtrack = self._invertClassDef(sub.BacktrackClassDef.classDefs, self.font)
        lookahead = {}
        if sub.LookAheadClassDef:
            lookahead = self._invertClassDef(sub.LookAheadClassDef.classDefs, self.font)
        inputs = {}
        if sub.InputClassDef:
            inputs = self._invertClassDef(sub.InputClassDef.classDefs, self.font)

        rulesets = getattr(sub, rulesetattr)
        for classId, ruleset in enumerate(rulesets):
            if not ruleset:
                continue
            rules = getattr(ruleset, ruleattr)
            inputclass = inputs[classId]
            for r in rules:
                prefix = [backtrack[x] for x in r.Backtrack]
                input_ = [inputclass] + [inputs[x] for x in r.Input]
                suffix = [lookahead[x] for x in r.LookAhead]
                lookups = self._unparse_lookups(getattr(r, lookupattr))
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
