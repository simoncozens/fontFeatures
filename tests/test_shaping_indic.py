from fontFeatures import FontFeatures
from fontFeatures.jankyPOS.Buffer import Buffer
from fontFeatures.fontProxy import FontProxy
from fontFeatures.shaperLib.Shaper import Shaper
from fontTools.ttLib import TTFont
import unittest


class TestShapingIndic(unittest.TestCase):
    font = TTFont("tests/data/1735326da89f0818cd8c51a0600e9789812c0f94.ttf")

    def test_shaping_guru(self):
      ff = FontFeatures()
      buf = Buffer(FontProxy(self.font), unicodes=chr(0x0A51))
      shaper = Shaper(ff, FontProxy(self.font))
      shaper.execute(buf)
      self.assertEqual(buf.serialize(), "uni25CC+1044@<0,0>|udaatguru+0@<0,0>")

    def test_shaping_matra_reorder(self):
      ff = FontFeatures()
      buf = Buffer(FontProxy(self.font), unicodes="हि")
      shaper = Shaper(ff, FontProxy(self.font))
      shaper.execute(buf)
      # Force buffer to codepoints
      for i in buf.items:
        delattr(i, "glyph")
        delattr(i, "position")
      self.assertEqual(buf.serialize(), "093f|0939")
