import copy
from fontTools.ttLib.tables import otBase, otTables
from fontTools.ttLib import newTable
from collections import OrderedDict
import itertools


def buildGPOSGSUB(self, font):
    for tag in ["GSUB", "GPOS"]:
        table = makeTable(self, tag, font)
        fontTable = font[tag] = newTable(tag)
        fontTable.table = table


def arrangeByScripts(self):
    for r in self.routines:
        if any(rule.languages for rule in r.rules):
            self.partitionRoutine(r, lambda rule: tuple(rule.languages or []))

    for r in self.routines:
        r.languages = r.rules[0].languages # Guaranteed to be the same
        if r.languages:
            for ix,langpair in enumerate(r.languages):
                if langpair[1] == "*":
                    r.languages[ix] = (langpair[0], "dflt")
                if langpair[0] == "*":
                    r.languages[ix] = ("DFLT", langpair[1])
        else:
            r.languages = [("DFLT", "dflt")]

    self.hoist_languages()
    script_lang_pairs = []
    for script in self.scripts_and_languages.keys():
        for lang in self.scripts_and_languages[script]:
            script_lang_pairs.append((script, lang))

    the_big_map = OrderedDict()
    def put_in_map(tag, script, lang, routine):
        key = (tag, script, lang)
        if key not in the_big_map:
            the_big_map[key] = []
        if routine not in the_big_map[key]:
            the_big_map[key].append(routine)

    def put_in_map_with_default(tag, script, lang, routine):
        put_in_map(tag, script, lang, routine)
        for script2, lang2 in script_lang_pairs:
            if script == "DFLT" and lang == "dflt":
                put_in_map(tag, script2, lang2, routine)
            elif script == script2 and lang == "dflt":
                put_in_map(tag, script2, lang2, routine)

    for tag, routinereferences in self.features.items():
        for r in routinereferences:
            for script, lang in r.routine.languages:
                put_in_map_with_default(tag, script, lang, r)

    return the_big_map

def separate_by_stage(the_big_map, stage):
    stage_map = OrderedDict()
    for k,v in the_big_map.items():
        v = [r for r in v if r.stage == stage]
        if v:
            stage_map[k] = v
    return stage_map

def makeTable(self, tag, font):
    table = getattr(otTables, tag, None)()
    table.Version = 0x00010000
    table.ScriptList = otTables.ScriptList()
    table.ScriptList.ScriptRecord = []
    table.FeatureList = otTables.FeatureList()
    table.FeatureList.FeatureRecord = []
    table.LookupList = otTables.LookupList()

    stage_map = separate_by_stage(arrangeByScripts(self), tag[1:].lower())
    stage_routines = [x for x in self.routines if x.stage == tag[1:].lower() ]
    lookups = [ x.toOTLookup(font) for x in stage_routines ]

    table.LookupList.Lookup = lookups

    # Build a table for mapping (tag, lookup_indices) to feature_index.
    # For example, ('liga', (2,3,7)) --> 23.
    feature_indices = {}
    required_feature_indices = {}  # ('latn', 'DEU') --> 23
    scripts = {}  # 'latn' --> {'DEU': [23, 24]} for feature #23,24
    # Sort the feature table by feature tag:
    # https://github.com/fonttools/fonttools/issues/568
    sortFeatureTag = lambda f: (f[0][2], f[0][1], f[0][0], f[1])
    for key, lookups in sorted(stage_map.items(), key=sortFeatureTag):
        feature_tag, script, lang = key
        # l.lookup_index will be None when a lookup is not needed
        # for the table under construction. For example, substitution
        # rules will have no lookup_index while building GPOS tables.
        lookup_indices = tuple([stage_routines.index(x.routine) for x in lookups ])

        size_feature = tag == "GPOS" and feature_tag == "size"
        if len(lookup_indices) == 0 and not size_feature:
            continue

        feature_key = (feature_tag, lookup_indices)
        feature_index = feature_indices.get(feature_key)
        if feature_index is None:
            feature_index = len(table.FeatureList.FeatureRecord)
            frec = otTables.FeatureRecord()
            frec.FeatureTag = feature_tag
            frec.Feature = otTables.Feature()
            # frec.Feature.FeatureParams = self.buildFeatureParams(feature_tag)
            frec.Feature.LookupListIndex = list(lookup_indices)
            frec.Feature.LookupCount = len(lookup_indices)
            table.FeatureList.FeatureRecord.append(frec)
            feature_indices[feature_key] = feature_index
        scripts.setdefault(script, {}).setdefault(lang, []).append(feature_index)

    # Build ScriptList.
    for script, lang_features in sorted(scripts.items()):
        srec = otTables.ScriptRecord()
        srec.ScriptTag = script
        srec.Script = otTables.Script()
        srec.Script.DefaultLangSys = None
        srec.Script.LangSysRecord = []
        for lang, feature_indices in sorted(lang_features.items()):
            langrec = otTables.LangSysRecord()
            langrec.LangSys = otTables.LangSys()
            langrec.LangSys.LookupOrder = None
            langrec.LangSys.ReqFeatureIndex = 0xFFFF
            langrec.LangSys.FeatureIndex = [i for i in feature_indices ]
            langrec.LangSys.FeatureCount = len(langrec.LangSys.FeatureIndex)
            if lang == "dflt":
                srec.Script.DefaultLangSys = langrec.LangSys
            else:
                langrec.LangSysTag = lang
                srec.Script.LangSysRecord.append(langrec)
        srec.Script.LangSysCount = len(srec.Script.LangSysRecord)
        table.ScriptList.ScriptRecord.append(srec)

    table.ScriptList.ScriptCount = len(table.ScriptList.ScriptRecord)
    table.FeatureList.FeatureCount = len(table.FeatureList.FeatureRecord)
    table.LookupList.LookupCount = len(table.LookupList.Lookup)
    return table
