#!/usr/bin/env python
import logging
import os
import sys
from argparse import ArgumentParser
from collections import OrderedDict

import fontTools.feaLib.ast as feaast
import glyphsLib
from fontTools.ttLib import TTFont
from glyphsLib.classes import GSAnchor, GSClass, GSFeature, GSFeaturePrefix, Point

import fontFeatures
from fontFeatures.feaLib.FontFeatures import add_language_system_statements
from fontFeatures.ttLib import unparse
from fontFeatures.ttLib.GDEFUnparser import GDEFUnparser

LOGLEVEL = os.environ.get("LOGLEVEL", "WARNING").upper()
logging.basicConfig(level=LOGLEVEL)

import warnings


def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    return "# [warning] %s\n" % (message)


warnings.formatwarning = warning_on_one_line

parser = ArgumentParser()
parser.add_argument("binary", help="binary font file to process", metavar="TTF")
parser.add_argument("source", help="source file to process", metavar="SOURCE")
parser.add_argument(
    "-o",
    "--output",
    dest="output",
    help="Output source file (defaults to overwriting original)",
)
parser.add_argument(
    "-i",
    "--index",
    dest="index",
    type=int,
    default=-1,
    help="Font index number (required for collections)",
)

parser.add_argument(
    "--config", default=None, help="config file to process", metavar="CONFIG"
)
args = parser.parse_args()

config = {}
if args.config:
    import json

    with open(args.config) as f:
        config = json.load(f)

if args.binary.endswith("c") and args.index == -1:
    print(
        "Must provide -i argument with TrueType/OpenType collection file",
        file=sys.stderr,
    )
    sys.exit(1)

font = TTFont(args.binary, fontNumber=args.index)
ff = unparse(font, do_gdef=True, doLookups=True, config=config)

glyphs = glyphsLib.load(open(args.source))

if not args.output:
    args.output = args.source

for feature in ["mark", "mkmk"]:
    if feature not in ff.features:
        continue

    mark = ff.features[feature]
    new_mark = []
    for rr in mark:
        routine = rr.routine
        delete_me = False
        for rule in routine.rules:
            if isinstance(rule, fontFeatures.Attachment):
                delete_me = True
                anchor_name = rule.base_name
                for base, pos in rule.bases.items():
                    anchor = GSAnchor(name=anchor_name, position=Point(*pos))
                    glyph = glyphs.glyphs[base]
                    if len(glyph.layers) > 1:
                        raise NotImplementedError("Can't deal with variable fonts yet")
                    glyph.layers[0].anchors.append(anchor)
                anchor_name = "_" + rule.base_name
                for mark, pos in rule.marks.items():
                    anchor = GSAnchor(name=anchor_name, position=Point(*pos))
                    glyph = glyphs.glyphs[mark]
                    if len(glyph.layers) > 1:
                        raise NotImplementedError("Can't deal with variable fonts yet")
                    glyph.layers[0].anchors.append(anchor)
        if not delete_me:
            new_mark.append(rr)
        else:
            del ff.routines[ff.routines.index(routine)]
    ff.features[feature] = new_mark

# kern

for feature in ["kern", "dist"]:
    if feature not in ff.features:
        continue
    kern = ff.features[feature]
    new_kern = []
    for rr in kern:
        routine = rr.routine
        delete_me = False
        for rule in routine.rules:
            if isinstance(rule, fontFeatures.Positioning):
                # Is it pair positioning
                if len(rule.glyphs) != 2:
                    break
                # Is it a simple kern?
                if not (rule.valuerecords[0] and not rule.valuerecords[1]):
                    break
                for left in rule.glyphs[0]:
                    for right in rule.glyphs[1]:
                        glyphs.setKerningForPair(
                            glyphs.masters[0].id,
                            left,
                            right,
                            rule.valuerecords[0].xAdvance,
                        )
                        print(
                            "# Kerning %s %s = %i"
                            % (left, right, rule.valuerecords[0].xAdvance)
                        )
                    delete_me = True

        if not delete_me:
            new_kern.append(rr)
        else:
            del ff.routines[ff.routines.index(routine)]
    ff.features[feature] = new_kern


# Fix GDEF classes
for glyph, cat in ff.glyphclasses.items():
    if cat == "mark":
        glyphs.glyphs[glyph].category = "Mark"
        glyphs.glyphs[glyph].subCategory = "Nonspacing"

# Put other features into Glyphs

# Named classes
first = ff.asFea()
for cls, members in ff.namedClasses.items():
    glyphs.classes.append(GSClass(name=cls, code=" ".join(members)))

# Lookups go into prefix, in order of dependency
def add_feature_prefix(routine):
    glyphs.featurePrefixes.append(
        GSFeaturePrefix(name=routine.name, code=routine.asFea())
    )


queue = list(ff.routines)
seen = {}
while queue:
    for dep in queue[0].dependencies:
        if not dep in seen:
            queue.insert(0, dep)
    routine = queue.pop(0)
    if not routine in seen:
        add_feature_prefix(routine)
    seen[routine] = True


# All the routine references go into a feature

# Work around https://github.com/googlefonts/ufo2ft/issues/506
if "mark" not in ff.features and "mkmk" in ff.features:
    newfeatures = OrderedDict()
    for k, v in ff.features.items():
        if k == "mkmk":
            newfeatures["mark"] = []
        newfeatures[k] = v
    ff.features = newfeatures

for featuretag, routines in ff.features.items():
    code = "\n".join([routine.asFea() for routine in routines])
    if featuretag in ["mark", "mkmk", "dist", "kern"]:
        code = "# Automatic Code Start\n" + code
    glyphs.features.append(GSFeature(name=featuretag, code=code))

# Add the language systems prefix
code = ""
for script, langs in ff.scripts_and_languages.items():
    for lang in langs:
        code += f"languagesystem {script} {lang};\n"
glyphs.featurePrefixes.append(GSFeaturePrefix(name="Languagesystems", code=code))

# Resolve duplicate anchors
#  Get names of all anchors
glyphs_with_anchor = {}
for g in glyphs.glyphs:
    for l in g.layers:
        for a in l.anchors:
            glyphs_with_anchor.setdefault(a.name, set()).add(g.name)

our_anchors = [a for a in glyphs_with_anchor.keys() if "Anchor" in a]
their_anchors = [a for a in glyphs_with_anchor.keys() if "Anchor" not in a]
drop_anchors = set()
if their_anchors:
    for theirs in their_anchors:
        for ours in our_anchors:
            if glyphs_with_anchor[theirs] != glyphs_with_anchor[ours]:
                continue
            same = True
            for g in glyphs_with_anchor[theirs]:
                for l in glyphs.glyphs[g].layers:
                    if l.anchors[theirs].position != l.anchors[ours].position:
                        same = False
            if not same:
                continue
            print("Our anchor '%s' was duplicate of original source '%s'" % (ours, theirs))
            drop_anchors.add(ours)
            break

for to_drop in drop_anchors:
    for glyph in glyphs_with_anchor[to_drop]:
        for l in glyphs.glyphs[glyph].layers:
            del l.anchors[to_drop]

glyphs.save(args.output)
