# Code for converting a Routine object into feaLib statements
import fontTools.feaLib.ast as feaast

def asFeaAST(self):
  if self.languages and len(self.languages) > 1:
    raise ValueError("Can't unparsed shared routine yet")
  # Arrange into rules of similar type
  if self.name:
    f = feaast.LookupBlock(name = self.name)
  else:
    f = feaast.Block()
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
