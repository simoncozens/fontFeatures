from fontFeatures import FontFeatures
from fontFeatures.jankyPOS.Buffer import Buffer
from fontFeatures.fontProxy import FontProxy
from fontFeatures.shaperLib.Shaper import Shaper
from fontFeatures.shaperLib.ArabicShaper import ArabicShaper
from fontTools.ttLib import TTFont
from fontFeatures.ttLib import unparse
import unittest

def u(*l):
  return "".join([chr(x) for x in l])

class TestShapingArabic(unittest.TestCase):
    font = TTFont("tests/data/Amiri-Regular.ttf")
    ff = unparse(font)

    def test_joining_1(self):
      buf = Buffer(FontProxy(self.font), unicodes=u(0x633,0x627))
      shaper = Shaper(self.ff, FontProxy(self.font))
      shaper.execute(buf)
      self.assertIsInstance(shaper.complexshaper, ArabicShaper)
      self.assertEqual(buf.serialize("arabic_joining", position=False), "uni0633.init(init)|uni0627.fina(fina)")

    def test_joining_2(self):
      buf = Buffer(FontProxy(self.font), unicodes=u(0x633,0x633,0x627))
      shaper = Shaper(self.ff, FontProxy(self.font))
      shaper.execute(buf)
      self.assertIsInstance(shaper.complexshaper, ArabicShaper)
      self.assertEqual(buf.serialize("arabic_joining", position=False), "uni0633.init(init)|uni0633.medi(medi)|uni0627.fina(fina)")
