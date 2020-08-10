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
name, and a class filter, which is either ``marks`` or ``bases``. It collects
all the glyphs which have anchors defined, and filters them according to their
class definition in the ``GDEF`` table. In this case, we have asked for ``bases``,
so glyph ``A`` will be selected. Then it looks for anchor definitions containing
the mark anchor name (here ``_top``), which will select ``acutecomb``, and
writes an attachment rule to tie them together. As shown in the example, this
is the most efficient way of expressing a mark-to-base feature.

Writing a mark-to-mark feature is similar; you just need to define a corresponding
anchor on the mark, and use the ``marks`` class filter instead of the ``bases``
filter::

      Anchors acutecomb { _top <-570 1290> top <-570 1650> };
      Feature mkmk { Attach &top &_top marks; };

fontFeatures will emit the correct mark-to-base or mark-to-mark lookup type based
on the ``GDEF`` class definition of the "base" glyph.
"""

class Anchors:
    takesBlock = True

    @classmethod
    def validateBlock(self, token, block, verbaddress):
        from ..parserTools import ParseContext
        from fontFeatures.parserTools import ParseError
        import re

        b = ParseContext(block)
        names = []
        while b.moreToParse:
            name = b.consumeToken().token
            if name in names:
                raise ParseError("Repeated anchor %s" % name, token.address, self)
            names.append(name)
            x = b.consumeToken()
            if not re.match("^<-?[\\d.]+$", x.token):
                raise ParseError(
                    "Invalid X coordinate for %s anchor" % name, token.address, self
                )
            y = b.consumeToken()
            if not re.match("^-?[\\d.]+>$", y.token):
                raise ParseError(
                    "Invalid Y coordinate for %s anchor" % name, token.address, self
                )
        return True

    @classmethod
    def storeBlock(self, parser, token, block):
        from ..parserTools import ParseContext

        glyphs = parser.expandGlyphOrClassName(token.token)
        anchors = {}
        b = ParseContext(block)
        while b.moreToParse:
            name = b.consumeToken().token
            x = b.consumeToken().token
            y = b.consumeToken().token
            anchors[name] = (int(x[1:]), int(y[:-1]))  # Or float?

        for g in glyphs:
            if not g in parser.fea.anchors:
                parser.fea.anchors[g] = {}
            parser.fea.anchors[g].update(anchors)

        return []


class Attach:
    takesBlock = False

    @classmethod
    def validate(self, tokens, verbaddress):
        from fontFeatures.parserTools import ParseError

        if len(tokens) < 2 or len(tokens) > 3:
            raise ParseError("Wrong number of arguments", token[0].address, self)
        if not (tokens[0].token.startswith("&")):
            raise ParseError("Anchor class should start with &", token[0].address, self)
        if not (tokens[1].token.startswith("&")):
            raise ParseError("Anchor class should start with &", token[1].address, self)
        if len(tokens) == 3 and (
            tokens[2].token != "bases" and tokens[2].token != "marks"
        ):
            raise ParseError(
                "Anchor filter should be 'marks' or 'bases'", token[2].address, self
            )
        return True

    @classmethod
    def store(self, parser, tokens, doFilter=None):
        from glyphtools import categorize_glyph
        import fontFeatures

        aFrom = tokens[0].token[1:]
        aTo = tokens[1].token[1:]
        bases = {}
        marks = {}
        for k, v in parser.fea.anchors.items():
            if aFrom in v:
                bases[k] = v[aFrom]
            if aTo in v:
                marks[k] = v[aTo]
        if len(tokens) == 3:
            if tokens[2].token == "bases":
                bases = {
                    k: v
                    for k, v in bases.items()
                    if categorize_glyph(parser.font, k)[0] == "base"
                }
            else:
                bases = {
                    k: v
                    for k, v in bases.items()
                    if categorize_glyph(parser.font, k)[0] == "mark"
                }
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
