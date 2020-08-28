"""
Anchor Management
=================

The ``Anchors`` plugin provides the ``Anchors`` and ``Attach`` verbs.

``Anchors`` takes a glyph name and a block containing anchor names and
positions, like so::

      Anchors A { top <679 1600> bottom <691 0> };

Note that there are no semicolons between anchors. The *same thing* happens
for mark glyphs::

      Anchors acutecomb { _top <-570 1290> };

Once all your anchors are defined, the ``Attach`` verb can be used to attach
marks to bases::

      Feature mark { Attach &top &_top bases; };

The ``Attach`` verb takes three parameters: a base anchor name, a mark anchor
name, and a class filter, which is either ``marks``, ``bases`` or ``cursive``.
The verb acts by collecting all the glyphs which have anchors defined, and
filtering them according to their class definition in the ``GDEF`` table.
In this case, we have asked for ``bases``, so glyph ``A`` will be selected.
Then it looks for anchor definitions containing the mark anchor name
(here ``_top``), which will select ``acutecomb``, and writes an attachment
rule to tie them together. As shown in the example, this
is the most efficient way of expressing a mark-to-base feature.

Writing a mark-to-mark feature is similar; you just need to define a corresponding
anchor on the mark, and use the ``marks`` class filter instead of the ``bases``
filter::

      Anchors acutecomb { _top <-570 1290> top <-570 1650> };
      Feature mkmk { Attach &top &_top marks; };

Writing a cursive attachment figure can be done by defining ``entry`` and ``exit``
anchors, and using an ``Attach`` statement like the following::

        Feature curs {
            Routine { Attach &entry &exit cursive; } IgnoreMarks;
        };

"""

from glyphtools import categorize_glyph
import fontFeatures

GRAMMAR = """
Anchors_Args = glyphselector:gs ws '{' ws (anchor_def)+:a ws '}' -> [gs, a]
anchor_def = <(letter|digit|"."|"_")+>:anchorname ws '<' integer:x ws integer:y '>' ws -> {"name":anchorname, "x": x, "y": y}

Attach_Args = '&' <(letter|digit|"."|"_")+>:anchor1 ws '&' <(letter|digit|"."|"_")+>:anchor2 ws ("marks"|"bases"|"cursive"):attachtype -> [anchor1, anchor2, attachtype]
"""

VERBS = ["Anchors", "Attach"]

class Anchors:
    @classmethod
    def action(self, parser, glyphselector, anchors):
        glyphs = glyphselector.resolve(parser.fontfeatures, parser.font)
        for g in glyphs:
            if not g in parser.fontfeatures.anchors:
                parser.fontfeatures.anchors[g] = {}
            for a in anchors:
                parser.fontfeatures.anchors[g][a["name"]] = (a["x"], a["y"])

        return []


class Attach:
    @classmethod
    def action(self, parser, aFrom, aTo, attachtype):
        bases = {}
        marks = {}
        for k, v in parser.fontfeatures.anchors.items():
            if aFrom in v:
                bases[k] = v[aFrom]
            if aTo in v:
                marks[k] = v[aTo]
            if attachtype == "marks":
                bases = {
                    k: v
                    for k, v in bases.items()
                    if categorize_glyph(parser.font, k)[0] == "mark"
                }
            else:
                bases = {
                    k: v
                    for k, v in bases.items()
                    if categorize_glyph(parser.font, k)[0] == "base"
                }
            if attachtype != "cursive":
                marks = {
                    k: v
                    for k, v in marks.items()
                    if categorize_glyph(parser.font, k)[0] == "mark"
                }
        return [
            fontFeatures.Routine(
                rules=[
                    fontFeatures.Attachment(aFrom, aTo, bases, marks, font=parser.font)
                ]
            )
        ]


# Dumping this here - script to export Anchors FEE from a FontFeatures object
# import itertools
# flatten = itertools.chain.from_iterable
# mark = list(flatten([x.rules for x in parsed.features["mark"]]))
# mkmk = list(flatten([x.rules for x in parsed.features["mkmk"]]))
# allfeat = mark + mkmk
# for f in allfeat:
#     for b in f.bases.keys():
#         if not b in parsed.anchors:
#             parsed.anchors[b] = {}
#         parsed.anchors[b][f.base_name] = f.bases[b]
#     for b in f.marks.keys():
#         if not b in parsed.anchors:
#             parsed.anchors[b] = {}
#         parsed.anchors[b][f.mark_name] = f.marks[b]

# for glyph in parsed.anchors.keys():
#     print("Anchors %s {" % glyph)
#     for name, anchor in parsed.anchors[glyph].items():
#         print("\t%s <%i %i>" % (name, *anchor))
#     print("};")
