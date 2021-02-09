"""
Anchor Management
=================

The ``Anchors`` plugin provides the ``Anchors``, ``LoadAnchors`` and ``Attach`` verbs.

``Anchors`` takes a glyph name and a block containing anchor names and
positions, like so::

      Anchors A { top <679 1600> bottom <691 0> };

Note that there are no semicolons between anchors. The *same thing* happens
for mark glyphs::

      Anchors acutecomb { _top <-570 1290> };

If you don't want to define these anchors manually but instead are dealing with
a source font file which contains anchor declarations, you can load the anchors
automatically from the font by using the ``LoadAnchors;`` verb.

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

from . import HelperTransformer
import fontFeatures

PARSEOPTS = dict(use_helpers=True)

GRAMMAR = ""

Anchors_GRAMMAR = """
?start: action
action: glyphselector anchors
anchors: anchor+
anchor: BARENAME "<" integer_container integer_container ">"
"""

Attach_GRAMMAR = """
?start: action
action: "&" BARENAME "&" BARENAME ATTACHTYPE
ATTACHTYPE: "marks" | "bases" | "cursive"
"""

LoadAnchors_GRAMMAR = """
?start: action
action:
"""

#"""
#Anchors_Args = glyphselector:gs ws '{' ws (anchor_def)+:a ws '}' -> [gs, a]
#anchor = <(letter|digit|"."|"_")+>
#anchor_def = anchor:anchorname ws '<' integer:x ws integer:y '>' ws -> {"name":anchorname, "x": x, "y": y}
#Attach_Args = '&' anchor:anchor1 ws '&' anchor:anchor2 ws ("marks"|"bases"|"cursive"):attachtype -> [anchor1, anchor2, attachtype]
#
#LoadAnchors_Args = ws -> ()
#"""

VERBS = ["Anchors", "Attach", "LoadAnchors"]

class Anchors(HelperTransformer):
    def anchors(self, args):
        return args

    def anchor(self, args):
        (name, x, y) = args
        name = name.value
        return (name, x, y)

    def action(self, args):
        (glyphselector, anchors) = args

        glyphs = glyphselector.resolve(self.parser.fontfeatures, self.parser.font)
        for g in glyphs:
            if not g in self.parser.fontfeatures.anchors:
                self.parser.fontfeatures.anchors[g] = {}
            for a in anchors:
                (name, x, y) = a
                self.parser.fontfeatures.anchors[g][name] = (x, y)

        return []

class LoadAnchors(HelperTransformer):
    def action(self, _):
        for glyphname in self.parser.font.exportedGlyphs():
            g = self.parser.font[glyphname]
            for a in g.anchors:
                if not g.name in self.parser.fontfeatures.anchors:
                    self.parser.fontfeatures.anchors[g.name] = {}
                self.parser.fontfeatures.anchors[g.name][a.name] = (a.x, a.y)

class Attach(HelperTransformer):
    def action(self, args):
        (aFrom, aTo, attachtype) = args    

        bases = {}
        marks = {}
        def _category(k):
            return self.parser.fontfeatures.glyphclasses.get(k, self.parser.font[k].category)

        for k, v in self.parser.fontfeatures.anchors.items():
            if aFrom in v:
                bases[k] = v[aFrom]
            if aTo in v:
                marks[k] = v[aTo]
            if attachtype == "marks":
                bases = {
                    k: v
                    for k, v in bases.items()
                    if _category(k) == "mark"
                }
            else:
                bases = {
                    k: v
                    for k, v in bases.items()
                    if _category(k) == "base"
                }
            if attachtype != "cursive":
                marks = {
                    k: v
                    for k, v in marks.items()
                    if _category(k) == "mark"
                }
        return [
            fontFeatures.Routine(
                rules=[
                    fontFeatures.Attachment(aFrom, aTo, bases, marks, font=self.parser.font)
                ]
            )
        ]

