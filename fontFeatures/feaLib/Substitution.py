# Code for converting a Substitution object into feaLib statements
import fontTools.feaLib.ast as feaast
from fontFeatures.ttLib.Substitution import lookup_type

def glyphref(g):
  if len(g) == 1:
    return feaast.GlyphName(g[0])
  return feaast.GlyphClass([feaast.GlyphName(x) for x in g])

def gensym(ff):
  if not "index" in ff.scratch:
    ff.scratch["index"] = 0
  ff.scratch["index"] = ff.scratch["index"] + 1
  return str(ff.scratch["index"])

def replaceLongWithClasses(i, ff):
  for ix,gc in enumerate(i):
    if len(gc) > 5:
      if not tuple(sorted(gc)) in ff.scratch["glyphclasses"]:
        classname = "class"+gensym(ff)
        ff.namedClasses[classname] = gc
        ff.scratch["glyphclasses"][tuple(sorted(gc))] = classname
      else:
        classname = ff.scratch["glyphclasses"][tuple(sorted(gc))]
      i[ix] = ["@"+classname]

def feaPreamble(self, ff):
  if not "glyphclasses" in ff.scratch:
    ff.scratch["glyphclasses"] = {}
  replaceLongWithClasses(self.input, ff)
  replaceLongWithClasses(self.precontext, ff)
  replaceLongWithClasses(self.postcontext, ff)
  replaceLongWithClasses(self.replacement, ff)

  return []

def asFeaAST(self):
  lut = lookup_type(self)
  if lut == 3:
    return feaast.AlternateSubstStatement(
      [glyphref(x) for x in self.precontext],
      glyphref(self.input[0]),
      [glyphref(x) for x in self.postcontext],
      feaast.GlyphClass([feaast.GlyphName(x) for x in self.replacement[0]])
    )
  elif lut == 1:
    return feaast.SingleSubstStatement(
      [glyphref(x) for x in self.input],
      [glyphref(x) for x in self.replacement],
      [glyphref(x) for x in self.precontext],
      [glyphref(x) for x in self.postcontext],
      False
    )
  elif lut == 4:
    return feaast.LigatureSubstStatement(
      [glyphref(x) for x in self.precontext],
      [glyphref(x) for x in self.input],
      [glyphref(x) for x in self.postcontext],
      glyphref(self.replacement[0]),
      False
    )
  elif lut == 9:
    raise ValueError
  elif lut == 2:
    return feaast.MultipleSubstStatement(
    [glyphref(x) for x in self.precontext],
    glyphref(self.input[0]),
    [glyphref(x) for x in self.postcontext],
    [glyphref(x) for x in self.replacement])

  import warnings
  warnings.warn("Couldn't convert Substitution Lookup Type %i" % lut)
  raise ValueError()
