# Code for converting a Attachment object into feaLib statements
import fontTools.feaLib.ast as feaast

def glyphref(g):
  if len(g) == 1:
    return feaast.GlyphName(g[0])
  return feaast.GlyphClass([feaast.GlyphName(x) for x in g])

def sortByAnchor(self):
  anchors = {}
  for mark in self.marks:
    if not mark[1] in anchors:
      anchors[mark[1]] = []
    anchors[mark[1]].append(mark[0])
  self.marks =  [ (v, k) for k, v in anchors.items()]

  anchors = {}
  for base in self.bases:
    if not base[1] in anchors:
      anchors[base[1]] = []
    anchors[base[1]].append(base[0])
  self.bases =  [ (v, k) for k, v in anchors.items() ]

def asFeaAST(self):
  b = feaast.Block()
  sortByAnchor(self)
  for mark in self.marks:
    b.statements.append(feaast.MarkClassDefinition(
      feaast.MarkClass(self.base_name),
      feaast.Anchor(*mark[1]),
      glyphref(mark[0])
    ))
  for base in self.bases:
    b.statements.append(feaast.MarkBasePosStatement(
      glyphref(base[0]),
      [[
        feaast.Anchor(*base[1]),
        feaast.MarkClass(self.base_name)
      ]]
    ))

  return b

