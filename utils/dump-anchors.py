import itertools
from fontFeatures.ttLib import unparse
from argparse import ArgumentParser
from fontTools.ttLib import TTFont


parser = ArgumentParser()
parser.add_argument("input", help="font file to process", metavar="FILE")
args = parser.parse_args()
font = TTFont(args.input)
parsed = unparse(font)

flatten = itertools.chain.from_iterable
mark = list(flatten([x.rules for x in parsed.features["mark"]]))
mkmk = list(flatten([x.rules for x in parsed.features["mkmk"]]))
allfeat = mark + mkmk

import code; code.interact(local=locals())

for f in allfeat:
    for b in f.bases.keys():
        if not b in parsed.anchors:
            parsed.anchors[b] = {}
        parsed.anchors[b][f.base_name] = f.bases[b]
    for b in f.marks.keys():
        if not b in parsed.anchors:
            parsed.anchors[b] = {}
        parsed.anchors[b][f.mark_name] = f.marks[b]

for glyph in parsed.anchors.keys():
    print("Anchors %s {" % glyph)
    for name, anchor in parsed.anchors[glyph].items():
        print("\t%s <%i %i>" % (name, *anchor))
    print("};")
