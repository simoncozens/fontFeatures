# Code for converting a Routine object into feaLib statements
import fontTools.feaLib.ast as feaast
from fontFeatures.ttLib.Substitution import lookup_type as sub_lookup_type
from fontFeatures.ttLib.Positioning import lookup_type as pos_lookup_type

def feaPreamble(self, ff):
    preamble = []
    return preamble


def asFeaAST(self):
    return feaast.LookupReferenceStatement(self.routine.asFeaAST())


def asFea(self):
    return self.asFeaAST().asFea()
