from fontTools.misc.py23 import *
import fontTools
from fontTools.feaLib.ast import *
from collections import OrderedDict

class GTableUnparser:
    def __init__(self, table, ff, languageSystems):
        self.table = table.table
        self.feature = ff
        self.lookupNames = []
        self.index = 0
        self.lookups = {}
        self.languageSystems = languageSystems
        self.sharedLookups = set([])

    def gensym(self):
        self.index = self.index + 1
        return str(self.index)

    def unparse(self):
        self.unparseLookups()
        self.collectFeatures()
        self.tidyFeatures()
        self.addFeatures()

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
                self._prepareFeatureLangSys('dflt', scriptRecord.Script.DefaultLangSys, self.table, features, scriptTag)
            for langSysRecord in scriptRecord.Script.LangSysRecord:
                self._prepareFeatureLangSys(langSysRecord.LangSysTag, langSysRecord.LangSys, self.table, features, scriptTag)
        self.features = features

    def tidyFeatures(self):
        # Now tidy up. Most common case is a set of lookups duplicated to all language systems
        for name, feature in self.features.items():
            # print(feature["DFLT"]["dflt"])
            allLookups = [ langLookup for script in feature.values() for langLookup in script.values() ]
            lookupsAreEqual = [ x == allLookups[0] for x in allLookups ]
            if all(lookupsAreEqual):
                self.features[name] = { "DFLT": { "dflt": allLookups[0] }}

        # Also check for individual lookups which can be hoisted to default
        for name, feature in self.features.items():
            allLookups = [ langLookup for script in feature.values() for langLookup in script.values() ]
            for lookupIx in allLookups[0]:
                everyoneGetsIt = all([ lookupIx in x for x in allLookups ])
                if everyoneGetsIt and len(allLookups)>1:
                    for arr in allLookups[1:]:
                        arr.remove(lookupIx)

    def inlineFeatures(self):
        # Check which can be inlined and which are shared
        for name, feature in self.features.items():
            for script in feature.values():
                for langLookups in script.values():
                    for lookupIdx in langLookups:
                        self.lookups[lookupIdx]["useCount"] = self.lookups[lookupIdx]["useCount"]+1
                        if self.lookups[lookupIdx]["useCount"] > 1 and len(self.lookups[lookupIdx]["lookup"].statements) > 3:
                            self.lookups[lookupIdx]["inline"] = False
                            self.sharedLookups.add(lookupIdx)


    def addFeatures(self):
        self.feature.statements.append(Comment('\n# Shared lookups\n'))
        for l in self.sharedLookups:
            self.feature.statements.append(self.lookups[l]["lookup"])

        for name, feature in self.features.items():
            f = FeatureBlock(name=name)
            for scriptname, langs in feature.items():
                for lang, lookups in langs.items():
                    if not (scriptname == "DFLT" and lang == "dflt"):
                        f.statements.append(Comment(""))
                        f.statements.append(ScriptStatement(scriptname))
                        f.statements.append(LanguageStatement(lang))
                    for lookupIdx in lookups:
                        lookup = self.lookups[lookupIdx]["lookup"]
                        if self.lookups[lookupIdx]["inline"]:
                            for s in lookup.statements:
                                f.statements.append(s)
                        else:
                            f.statements.append(LookupReferenceStatement(lookup))
            self.feature.statements.append(f)

    def unparseLookups(self):
        lookupOrder = range(0,len(self.table.LookupList.Lookup))
        # Reorder to check for dependencies
        newOrder = []
        while True:
            changed = False
            newOrder = []
            for lookupIdx in lookupOrder:
                lookup = self.table.LookupList.Lookup[lookupIdx]
                if lookup.LookupType == 6:
                    for sub in lookup.SubTable:
                        if hasattr(sub, "SubstLookupRecord"):
                            for sl in sub.SubstLookupRecord:
                                if not sl.LookupListIndex in newOrder:
                                    newOrder.append(sl.LookupListIndex)
                                    changed = True
                if not lookupIdx in newOrder:
                    newOrder.append(lookupIdx)
            lookupOrder = newOrder
            if not changed:
                break

        for lookupIdx in lookupOrder:
            lookup = self.table.LookupList.Lookup[lookupIdx]
            unparser = getattr(self, "unparse"+self.lookupTypes[lookup.LookupType])
            res, dependencies = unparser(lookup)
            self.lookups[lookupIdx] = {
                "lookup": res,
                "dependencies": dependencies,
                "useCount": 0,
                "inline": True
            }
