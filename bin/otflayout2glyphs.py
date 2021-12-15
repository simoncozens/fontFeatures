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

class Layout2Glyphs:
    def __init__(self, gsfont, ff):
        self.gsfont = gsfont
        self.ff = ff

    def process(self):
        for feature in ["mark", "mkmk"]:
            if feature in self.ff.features:
                self.add_anchors(feature)
        for feature in ["kern", "dist"]:
            if feature in ff.features:
                self.add_kerning(feature)
        self.fix_gdef_classes()
        self.add_named_classes()
        self.add_routines_to_feature_prefix()
        self.ensure_mark_mkmk()
        self.add_features_to_glyphs()
        self.add_language_systems()
        self.fix_duplicate_anchors()

    def add_anchor_to_glyph(self, glyphname, anchor_name, pos):
        anchor = GSAnchor(name=anchor_name, position=Point(*pos))
        glyph = self.gsfont.glyphs[glyphname]
        if len(glyph.layers) > 1:
            raise NotImplementedError("Can't deal with variable fonts yet")
        glyph.layers[0].anchors.append(anchor)

    def add_anchors(self, feature):
        mark = self.ff.features[feature]
        new_mark = []
        for rr in mark:
            routine = rr.routine
            delete_me = False
            for rule in routine.rules:
                if isinstance(rule, fontFeatures.Attachment):
                    delete_me = True
                    anchor_name = rule.base_name
                    for base, pos in rule.bases.items():
                        self.add_anchor_to_glyph(base, anchor_name, pos)
                    anchor_name = "_" + rule.base_name
                    for mark, pos in rule.marks.items():
                        self.add_anchor_to_glyph(mark, anchor_name, pos)
            if not delete_me:
                new_mark.append(rr)
            else:
                del self.ff.routines[self.ff.routines.index(routine)]
        self.ff.features[feature] = new_mark

    def add_kerning(self, feature):
        kern = self.ff.features[feature]
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
                            self.gsfont.setKerningForPair(
                                self.gsfont.masters[0].id,
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

    def fix_gdef_classes(self):
        for glyph, cat in self.ff.glyphclasses.items():
            if cat == "mark":
                self.gsfont.glyphs[glyph].category = "Mark"
                self.gsfont.glyphs[glyph].subCategory = "Nonspacing"

    def add_named_classes(self):
        ff.asFea()
        for cls, members in self.ff.namedClasses.items():
            self.gsfont.classes.append(GSClass(name=cls, code=" ".join(members)))

    def add_feature_prefix(self, routine):
        self.gsfont.featurePrefixes.append(
            GSFeaturePrefix(name=routine.name, code=routine.asFea())
        )

    def add_routines_to_feature_prefix(self):
        # Lookups go into prefix, in order of dependency
        queue = list(self.ff.routines)
        seen = {}
        while queue:
            for dep in queue[0].dependencies:
                if dep not in seen:
                    queue.insert(0, dep)
            routine = queue.pop(0)
            if routine not in seen:
                self.add_feature_prefix(routine)
            seen[routine] = True

    def ensure_mark_mkmk(self):
        # Work around https://github.com/googlefonts/ufo2ft/issues/506
        if "mark" not in self.ff.features and "mkmk" in self.ff.features:
            newfeatures = OrderedDict()
            for k, v in self.ff.features.items():
                if k == "mkmk":
                    newfeatures["mark"] = []
                newfeatures[k] = v
            self.ff.features = newfeatures

    def add_features_to_glyphs(self):
        for featuretag, routines in self.ff.features.items():
            code = "\n".join([routine.asFea() for routine in routines])
            if featuretag in ["mark", "mkmk", "dist", "kern"]:
                code = "# Automatic Code Start\n" + code
            self.gsfont.features.append(GSFeature(name=featuretag, code=code))

    def add_language_systems(self):
        code = ""
        for script, langs in self.ff.scripts_and_languages.items():
            for lang in langs:
                code += f"languagesystem {script} {lang};\n"
        self.gsfont.featurePrefixes.append(GSFeaturePrefix(name="Languagesystems", code=code))

    def fix_duplicate_anchors(self):
        #  Get names of all anchors
        glyphs_with_anchor = {}
        for g in self.gsfont.glyphs:
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
                        for l in self.gsfont.glyphs[g].layers:
                            if l.anchors[theirs].position != l.anchors[ours].position:
                                same = False
                    if not same:
                        continue
                    print("Our anchor '%s' was duplicate of original source '%s'" % (ours, theirs))
                    drop_anchors.add(ours)
                    break

        for to_drop in drop_anchors:
            for glyph in glyphs_with_anchor[to_drop]:
                for l in self.gsfont.glyphs[glyph].layers:
                    del l.anchors[to_drop]

font = TTFont(args.binary, fontNumber=args.index)
ff = unparse(font, do_gdef=True, doLookups=True, config=config)

gsfont = glyphsLib.load(open(args.source))

Layout2Glyphs(gsfont, ff).process()

if not args.output:
    args.output = args.source
gsfont.save(args.output)
print(f"Saved {args.output}")
