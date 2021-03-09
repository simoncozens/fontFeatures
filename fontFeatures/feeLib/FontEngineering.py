"""
Font Engineering
================

This plugin provides verbs which allow you to modify the font while processing
it. For example, it's common when engineering fonts for scripts with complex
requirements to create a set of glyphs which act purely as markers, which are
referred to by future substitution or positioning rules, or which connect to
alternate anchor points, or which are used to guide contextual rules.
These glyphs aren't part of the design, and it's annoying to have them sitting
around in the design source; they're really only a creation of the layout rules.
This plugin allows you to create and modify such glyphs within your features
file, so that they are available when needed but aren't getting in the designer's
way.

The `DuplicateGlyphs` verb takes two glyph selectors, one for the existing
glyphs and one for a new set of glyphs, and adds the new glyphs to the file
with the outlines, metrics and glyph category of the existing glyphs. For
example::

    DuplicateGlyphs /^[a-z]$/ /^[a-z]$/.alt;

This will create copies of all the lowercase Latin letters.

The `SetWidth` verb takes a glyph selector and a width, which is either absolute
(integer number of font units) or relative (percentage of existing width).
Relative widths are specified by a percent sign suffix. The width of the glyph
will be altered appropriately. Hence::

    DuplicateGlyphs space space.ARA;
    SetWidth space.ARA 50%;

This creates a new glyph `space.ARA` from the `space` glyph and then sets its
advance width to be 50% of the width of `space`.

The `SetCategory` verb sets a glyph's OpenType category::

    DuplicateGlyphs tonemark tonemark.spacing;
    SetCategory tonemark.spacing base;
    SetWidth tonemark.spacing 120;

"""

import warnings

from . import FEEVerb

GRAMMAR = ""

SetWidth_GRAMMAR = """
?start: action
action: glyphselector integer_container PERCENT?
PERCENT: "%"
"""

SetCategory_GRAMMAR = """
?start: action
action: glyphselector GLYPH_CATEGORY
GLYPH_CATEGORY: "base" | "mark" | "ligature" | "component"
"""

DuplicateGlyphs_GRAMMAR = """
?start: action
action: glyphselector glyphselector
"""

PARSEOPTS = dict(use_helpers=True)
VERBS = ["SetWidth", "SetCategory"]

class SetWidth(FEEVerb):
    def action(self, args):
        (glyphs, width, is_relative) = args
        for g in glyphs.resolve(self.parser.fontfeatures, self.parser.font):
            glyph = self.parser.font[g]
            if is_relative:
                glyph.width = glyph.width * width / 100
            else:
                glyph.width = width
        self.parser.font_modified = True
        return []

class DuplicateGlyphs:
    def action(self, parser, existing, new):
        oldglyphs = existing.resolve(self.parser.fontfeatures, self.parser.font)
        newglyphs = new.resolve(self.parser.fontfeatures, self.parser.font, mustExist = False)
        if len(oldglyphs) != len(newglyphs):
            raise ValueError(
                "Length of new glyphs should be the same as old glyphs"
            )
        for o,n in zip(oldglyphs, newglyphs):
            if n in self.parser.glyphs:
                warnings.warn("Glyph '%s' already exists" % n)
                continue
            oldglyph = parser.font[o]
            newglyph = o.copy()
            newglyph.name = n
            newglyph.category = oldglyph.category
            # XXX mark attachment class
            self.parser.font_modified = True
        self.parser.glyphs = list(parser.font.keys())
        return []

class SetCategory(FEEVerb):
    def action(self, args):
        glyphs = args[0]
        category = args[1].value
        for g in glyphs.resolve(self.parser.fontfeatures, self.parser.font):
            self.parser.fontfeatures.glyphclasses[g] = category
        return []

