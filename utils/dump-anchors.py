# Parse a GPOS ttx dump and output a cursive attachment .fea
import xml.etree.cElementTree as et
from fontTools.feaLib.ast import *

tree = et.parse("cursive.xml")
doc = tree.getroot()
glyphs = [x.attrib["value"] for x in tree.findall("Coverage/Glyph")]
recs = tree.findall("EntryExitRecord")

droplist = []
poslist = []
for i,rec in enumerate(recs):
  entries = rec.findall("EntryAnchor")
  exits   = rec.findall("ExitAnchor")
  if len(entries) > 0:
    entryY = int(entries[0].find("YCoordinate").attrib["value"])
    entryX = int(entries[0].find("XCoordinate").attrib["value"])
    entryAnchor = Anchor(entryX, entryY)
  else:
    entryY = 0
    entryAnchor = Anchor(0,0,name="NULL")

  if len(exits) > 0:
    exitY = int(exits[0].find("YCoordinate").attrib["value"])
    exitX = int(exits[0].find("XCoordinate").attrib["value"])
    exitAnchor = Anchor(exitX, exitY)
  else:
    exitY = 0
    exitAnchor = Anchor(0,0,name="NULL")

  drop = entryY - exitY
  droplist.append((glyphs[i],drop))
  poslist.append(CursivePosStatement(GlyphName(glyphs[i]), entryAnchor, exitAnchor))

droplist = sorted(droplist, key = lambda x:x[1])

import numpy as np

def groupByDrop(droplist, classname, bincount=10):
  relevant = list(filter(lambda x: classname in x[0] , droplist))
  dropValues = [ x[1] for x in relevant ]
  edges = np.histogram_bin_edges(dropValues, bins = bincount)
  middles = list((edges[0:-1] + edges[1:] ) /2)
  groups = np.digitize(dropValues, edges) -1

  binnedGlyphs = {}
  for i,group in enumerate(groups):
    if not group in binnedGlyphs:
      binnedGlyphs[group] = []
    binnedGlyphs[group].append(relevant[i][0])
  middles.append(edges[-1])
  classes = []
  for k,v in binnedGlyphs.items():
    classes.append(GlyphClassDefinition("%s_%i" % (classname,k), GlyphClass(v)))
    classes.append(Comment("# average drop = %i\n" % middles[k]))

  return binnedGlyphs, middles, classes

binnedMeds, medMiddles, medClasses = groupByDrop(droplist, "Med")
for x in medClasses:
  print(x.asFea())
binnedInis, iniMiddles, iniClasses = groupByDrop(droplist, "Ini")
for x in iniClasses:
  print(x.asFea())

binnedFins, finMiddles, finClasses = groupByDrop(droplist, "Fin")
for x in finClasses:
  print(x.asFea())

print("feature curs {\n")
print("lookupflag IgnoreMarks;\n")
for x in poslist:
  print(x.asFea())
print("} curs;")

# print("feature kern {\n")
# print("lookupflag IgnoreMarks;\n")

# for i in binnedInis.keys():
#   for m1 in binnedMeds.keys():
#     for f in binnedFins.keys():
#       totalDrop = (iniMiddles[i] + medMiddles[m1] + finMiddles[f])
#       print("\tposition @Ini_%i' <0 %i 0 0> @Med_%i @Fin_%i;" % (i, totalDrop, m1,f))

# for i in binnedInis.keys():
#   for m1 in binnedMeds.keys():
#     for m2 in binnedMeds.keys():
#       for f in binnedFins.keys():
#         totalDrop = (iniMiddles[i] + medMiddles[m1] + medMiddles[m2] + finMiddles[f])
#         print("\tposition @Ini_%i' <0 %i 0 0> @Med_%i  @Med_%i  @Fin_%i;" % (i, totalDrop, m1,m2,f))
#   print("} kern;")
