from fontTools.misc.py23 import *
import fontTools
from fontTools.feaLib.ast import *
from collections import OrderedDict

from .GDEFUnparser import GDEFUnparser
from .GSUBUnparser import GSUBUnparser

def unparseLanguageSystems(tables, featureFile):
    scripts = OrderedDict()
    for table in tables:
        for scriptRecord in table.table.ScriptList.ScriptRecord:
            scriptTag = scriptRecord.ScriptTag
            languages = scripts.get(scriptTag, [])
            script = scriptRecord.Script
            items = [];
            if script.DefaultLangSys is not None:
                items.append(('dflt', script.DefaultLangSys))
            items += [(l.LangSysTag, l.LangSys) for l in script.LangSysRecord]
            languages = set([i[0] for i in items])

            if languages and not scriptTag in scripts:
                scripts[scriptTag] = languages

    for script, languages in scripts.items():
        for language in languages:
            featureFile.statements.append(LanguageSystemStatement(script,language.strip()))
    return scripts

def unparse(font, do_gdef = False):
    gsub_gpos = [font[tableTag] for tableTag in ('GSUB', 'GPOS') if tableTag in font]
    ff = FeatureFile()

    languageSystems = unparseLanguageSystems(gsub_gpos, featureFile = ff)

    if 'GDEF' in font:
        table = GDEFUnparser(font["GDEF"]).unparse()
        if table:
            ff.statements.append(table)

    if 'GSUB' in font:
        GSUBUnparser(font["GSUB"], ff, languageSystems).unparse()

    # if 'GPOS' in font:
    #     unparseGPOS(font['GPOS'], featureFile = ff)
    return ff
