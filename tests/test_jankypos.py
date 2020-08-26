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
        self.assertEqual(self.janky.serialize_buffer(buf),
            "H+708@<0,0>|A+612@<0,0>|Z+618@<0,0>"
        )

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
        self.assertEqual(self.janky.serialize_buffer(buf),
            "H+708@<0,0>|A+732@<0,0>|Z+618@<0,0>"
        )

    def test_anchor(self):
        self.font = TTFont("fonts/Roboto-Regular.ttf")
        self.janky = JankyPos(self.font)

        buf = self.janky.positioning_buffer(["F", "acutecomb", "B"])
        s = Attachment("top", "top_", {"F": (619, 1612)}, {"acutecomb": (-570, 1290)})
        buf = self.janky.process_rules(buf, [s])
        # Harfbuzz has 52 here, not 57, but I am not sure why
        self.assertEqual(self.janky.serialize_buffer(buf),
            "F+1132@<0,0>|acutecomb+0@<57,322>|B+1275@<0,0>"
        )

    def test_urdu(self):
        font = TTFont("fonts/NotoNastaliqUrdu-Dummy.ttf")
        janky = JankyPos(font, direction="RTL")
        ff = unparse(font)
        buf = janky.positioning_buffer(["SeenIni", "SeenMed", "NoonxFin"])
        buf = janky.process_fontfeatures(buf, ff)
        # Note that this is technically incorrect, because we do not
        # currently support the RightToLeft flag of cursive attachments.
        self.assertEqual(janky.serialize_buffer(buf),
            "NoonxFin+749@<0,-558>|SeenMed+538@<0,-223>|SeenIni+607@<0,0>")
