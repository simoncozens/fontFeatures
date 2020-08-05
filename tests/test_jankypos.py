from fontFeatures import Positioning, ValueRecord, Attachment
from fontFeatures.jankyPOS import JankyPos
from fontFeatures.ttLib import unparse
from fontTools.ttLib import TTFont
import unittest


class TestPositioning(unittest.TestCase):
    font = TTFont("fonts/Amiri-Regular.ttf")
    janky = JankyPos(font)

    def test_buffer(self):
        buf = self.janky.positioning_buffer(["H", "A", "Z"])
        self.assertEqual(buf[0]["glyph"], "H")
        self.assertEqual(buf[0]["position"], ValueRecord(xAdvance=708))
        self.assertEqual(buf[1]["glyph"], "A")
        self.assertEqual(buf[1]["position"], ValueRecord(xAdvance=612))
        self.assertEqual(buf[2]["glyph"], "Z")
        self.assertEqual(buf[2]["position"], ValueRecord(xAdvance=618))

    # def test_buffer_rtl(self):
    #   buf = self.janky.positioning_buffer(["uni0633.init","uni0646.fina"], direction="RTL")
    #   self.assertEqual(buf[0]["glyph"], "uni0646.fina")
    #   self.assertEqual(buf[0]["position"], ValueRecord(xAdvance=615))
    #   self.assertEqual(buf[1]["glyph"], "uni0633.init")
    #   self.assertEqual(buf[1]["position"], ValueRecord(xAdvance=568))

    def test_single(self):
        buf = self.janky.positioning_buffer(["H", "A", "Z"])
        v = ValueRecord(xAdvance=120)
        s = Positioning([["A"]], [v])
        buf = self.janky.process_rules(buf, [s])
        self.assertEqual(buf[0]["glyph"], "H")
        self.assertEqual(buf[0]["position"].asFea(), ValueRecord(xAdvance=708).asFea())
        self.assertEqual(buf[1]["glyph"], "A")
        self.assertEqual(buf[1]["position"].asFea(), ValueRecord(xAdvance=732).asFea())
        self.assertEqual(buf[2]["glyph"], "Z")
        self.assertEqual(buf[2]["position"].asFea(), ValueRecord(xAdvance=618).asFea())

    def test_anchor(self):
        self.font = TTFont("fonts/Roboto-Regular.ttf")
        self.janky = JankyPos(self.font)

        buf = self.janky.positioning_buffer(["F", "acutecomb", "B"])
        s = Attachment("top", "top_", {"F": (619, 1612)}, {"acutecomb": (-570, 1290)})
        buf = self.janky.process_rules(buf, [s])
        self.assertEqual(buf[0]["glyph"], "F")
        self.assertEqual(buf[0]["position"].asFea(), ValueRecord(xAdvance=1132).asFea())
        self.assertEqual(buf[1]["glyph"], "acutecomb")
        # Harfbuzz has 52 here, not 57, but I am not sure why
        vr = ValueRecord(xAdvance=0, yAdvance=0, xPlacement=57, yPlacement=322)
        self.assertEqual(buf[1]["position"].asFea(), vr.asFea())
        self.assertEqual(buf[2]["glyph"], "B")
        self.assertEqual(buf[2]["position"].asFea(), ValueRecord(xAdvance=1275).asFea())

    def test_urdu(self):
        font = TTFont("fonts/NotoNastaliqUrdu-Dummy.ttf")
        janky = JankyPos(font)
        ff = unparse(font)
        buf = janky.positioning_buffer(["NoonxFin", "SeenMed", "SeenIni"])
        buf = janky.process_fontfeatures(buf, ff)
        self.assertEqual(buf[0]["glyph"], "NoonxFin")
        self.assertEqual(buf[0]["position"].asFea(), ValueRecord(xAdvance=750).asFea())
        self.assertEqual(buf[1]["glyph"], "SeenMed")
        self.assertEqual(
            buf[1]["position"].asFea(),
            ValueRecord(xAdvance=539, xPlacement=-1, yPlacement=335).asFea(),
        )
        self.assertEqual(buf[2]["glyph"], "SeenIni")
        self.assertEqual(
            buf[2]["position"].asFea(),
            ValueRecord(xAdvance=607, xPlacement=-2, yPlacement=558).asFea(),
        )
