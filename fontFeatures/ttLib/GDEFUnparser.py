from fontTools.misc.py23 import *
import fontTools
from fontTools.feaLib.ast import *
from collections import OrderedDict


class GDEFUnparser:
    def __init__(self, table):
        self.table = table.table
        self.feature = TableBlock("GDEF")
        self.preamble = []

    def unparse(self):
        if self.table.MarkAttachClassDef is not None:
            self.unparseMarkAttachClassDefinitions()

        if (
            hasattr(self.table, "MarkGlyphSetsDef")
            and self.table.MarkGlyphSetsDef is not None
        ):
            self.unparseMarkGlyphSetDefinitions()

        if self.table.GlyphClassDef is not None:
            self.unparseGlyphClassDefinitions()

        if self.table.AttachList is not None:
            self.unparseAttachList()

        if self.table.LigCaretList is not None:
            self.unparseLigCaretList()

        if len(self.feature.statements) > 0 or self.preamble:
            b = Block()
            b.statements.extend(self.preamble)
            b.statements.append(self.feature)
            return b

    def unparseMarkAttachClassDefinitions(self):
        self.preamble.append(Comment("# Mark attachment classes\n"))
        markAttachClassDef = self.table.MarkAttachClassDef
        attachClasses = {}

        for key, val in markAttachClassDef.classDefs.items():
            if not val in attachClasses:
                attachClasses[val] = GlyphClass()
            attachClasses[val].append(key)

        for key, val in attachClasses.items():
            self.preamble.append(
                GlyphClassDefinition("markClass_" + str(key), val)
            )

    def unparseMarkGlyphSetDefinitions(self):
        lines = []
        self.preamble.append(Comment("# Mark glyph set classes\n"))
        for idx, coverage in enumerate(self.table.MarkGlyphSetsDef.Coverage):
            glyphclass = GlyphClass()
            for g in coverage.glyphs:
                glyphclass.append(g)
            self.preamble.append(
                GlyphClassDefinition("markGlyphSet_" + str(idx), glyphclass)
            )

    def unparseGlyphClassDefinitions(self):
        classDefs = self.table.GlyphClassDef.classDefs
        classNames = {
            1: "GDEF_Base",  # Base glyph (single character, spacing glyph)
            2: "GDEF_Ligature",  # Ligature glyph (multiple character, spacing glyph)
            3: "GDEF_Mark",  # Mark glyph (non-spacing combining glyph)
            4: "GDEF_Component",  # Component glyph (part of single character, spacing glyph)
        }

        glyphClasses = {}
        for k, v in classNames.items():
            glyphClasses[v] = GlyphClass()

        for key, val in classDefs.items():
            glyphClasses[classNames[val]].append(key)

        # Use named classes for everything
        for k, v in glyphClasses.items():
            definition = GlyphClassDefinition(k, v)
            self.preamble.append(definition)
            glyphClasses[k] = GlyphClassName(definition)

        self.feature.statements.append(
            GlyphClassDefStatement(
                glyphClasses["GDEF_Base"],
                # Next two classes in funny order because ast.GlyphClassDefStatement
                # definition has them the wrong way around.
                glyphClasses["GDEF_Mark"],
                glyphClasses["GDEF_Ligature"],
                glyphClasses["GDEF_Component"],
            )
        )

    def unparseAttachList(self):
        for idx, glyph in enumerate(self.table.AttachList.Coverage.glyphs):
            attachmentPoints = self.table.AttachList.AttachPoint[idx]
            self.feature.statements.append(
                AttachStatement(GlyphName(glyph), attachmentPoints.PointIndex)
            )

    def unparseLigCaretList(self):
        ligCaretList = self.table.LigCaretList
        for idx, glyph in enumerate(ligCaretList.Coverage.glyphs):
            glyph = GlyphName(glyph)
            ligGlyph = ligCaretList.LigGlyph[idx]
            formats = list({cv.Format for cv in ligGlyph.CaretValue})
            assert (
                len(formats) == 1
            ), "Can't use different CaretValue formats in one LigatureCaret entry"
            caretsFormat = formats[0]
            if caretsFormat == 1:
                # Format == 1: Design units only
                # LigatureCaretByPos <glyph|glyphclass> <caret position value>+;
                values = [str(cv.Coordinate) for cv in ligGlyph.CaretValue]
                self.feature.statements.append(
                    LigatureCaretByPosStatement(glyph, values)
                )
            elif caretsFormat == 2:
                # Format == 2: Contour point
                values = [str(cv.CaretValuePoint) for cv in ligGlyph.CaretValue]
                self.feature.statements.append(
                    LigatureCaretByIndexStatement(glyph, values)
                )
            elif caretsFormat == 3:
                # Format == 3: Design units plus Device table
                self.feature.statements.append(
                    Comment("# LigatureCaretByDev found, but not implemented")
                )
