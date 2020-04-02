# Code for converting a Attachment object into feaLib statements
import fontTools.feaLib.ast as feaast

def glyphref(g):
  if len(g) == 1:
    return feaast.GlyphName(g[0])
  return feaast.GlyphClass([feaast.GlyphName(x) for x in g])

def asFeaAST(self):
  b = feaast.Block()
  for mark in self.marks:
    b.statements.append(feaast.MarkClassDefinition(
      feaast.MarkClass(self.base_name),
      feaast.Anchor(*mark[1]),
      glyphref([mark[0]])
    ))
  for base in self.bases:
    b.statements.append(feaast.MarkBasePosStatement(
      glyphref([base[0]]),
      [[
        feaast.Anchor(*base[1]),
        feaast.MarkClass(self.base_name)
      ]]
    ))

  return b

