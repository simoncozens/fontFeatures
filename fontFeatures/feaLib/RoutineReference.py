# Code for converting a Routine object into feaLib statements
import fontTools.feaLib.ast as feaast
from fontFeatures.ttLib.Substitution import lookup_type as sub_lookup_type
from fontFeatures.ttLib.Positioning import lookup_type as pos_lookup_type

def feaPreamble(self, ff):
    preamble = []
    return preamble


def asFeaAST(self, allLanguages=[("DFLT", "dflt")]):
    if set(allLanguages) == set(self.routine.languages):
        if self.routine.usecount == 1:
            return self.routine.asFeaAST(inFeature=True)
        return feaast.LookupReferenceStatement(self.routine.asFeaAST())
    f = feaast.Block()
    lastLang = 'dflt'
    for s,l in self.routine.languages:
        f.statements.append(feaast.ScriptStatement(s))
        if l != lastLang:
            f.statements.append(feaast.LanguageStatement("%4s" % l))
            lastLang = l
        f.statements.append(feaast.LookupReferenceStatement(self.routine.asFeaAST()))
    return f


def asFea(self):
    return self.asFeaAST().asFea()
