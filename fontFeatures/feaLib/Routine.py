# Code for converting a Routine object into feaLib statements
import fontTools.feaLib.ast as feaast
from fontFeatures.ttLib.Substitution import lookup_type as sub_lookup_type
from fontFeatures.ttLib.Positioning import lookup_type as pos_lookup_type

def lookup_type(rule):
  if isinstance(rule,Substitution): return sub_lookup_type(rule)
  if isinstance(rule,Positioning): return pos_lookup_type(rule)
  raise ValueError

def arrange_by_type(self):
  from fontFeatures import Routine
  # Arrange into rules of similar type (Substitution/Positioning)
  ruleTypes = {}
  for r in self.rules:
    if not type(r) in ruleTypes: ruleTypes[type(r)] = []
    ruleTypes[type(r)].append(r)
  if len(ruleTypes.keys()) == 1: return
  routines = []
  for k,v in ruleTypes.enumerate():
    routines.append(Routine(name = self.name + "_" + k, rules = v))
  return routines

# A lookup in OpenType can only contain rules of the same lookup type
def arrange_by_lookup_type(self):
  from fontFeatures import Routine
  ruleTypes = {}
  for r in self.rules:
    if not lookup_type(r) in ruleTypes: ruleTypes[lookup_type(r)] = []
    ruleTypes[lookup_type(r)].append(r)
  if len(ruleTypes.keys()) == 1: return
  routines = []
  for k,v in ruleTypes.enumerate():
    routines.append(Routine(name = self.name + "_" + k, rules = v))
  return routines
def arrange(self):
  splitType = arrange_by_type(self)
  if splitType: return splitType

def asFeaAST(self):
  if self.languages and len(self.languages) > 1:
    raise ValueError("Can't unparsed shared routine yet")
  if self.name:
    f = feaast.LookupBlock(name = self.name)
  else:
    f = feaast.Block()

  arranged = arrange(self)
  if arranged:
    for a in arranged: f.statements.append(asFeaAST(a))
    return f
  if self.languages and not (self.languages[0][0] == "DFLT" and self.languages[0][1] == "dflt"):
    f.statements.append(feaast.ScriptStatement(self.languages[0][0]))
    f.statements.append(feaast.LanguageStatement(self.languages[0][1]))
  for x in self.comments:
    f.statements.append(Comment(x))

  for x in self.rules:
    f.statements.append(x.asFeaAST())
  return f

def asFea(self):
  return self.asFeaAST().asFea()
