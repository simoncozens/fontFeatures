from fontFeatures import FontFeatures
from fontFeatures.shaperLib.Buffer import Buffer
from fontFeatures.shaperLib.Shaper import Shaper
from fontFeatures.shaperLib.ArabicShaper import ArabicShaper
from fontTools.ttLib import TTFont
from fontFeatures.ttLib import unparse
from babelfont import Babelfont
import unittest

def u(*l):
  return "".join([chr(x) for x in l])

class TestShapingArabic(unittest.TestCase):
    fontfile = "tests/data/Amiri-Regular.ttf"
    font = TTFont("tests/data/Amiri-Regular.ttf")
    ff = unparse(font)

    def test_joining_1(self):
      bbf = Babelfont.open(self.fontfile)
      buf = Buffer(bbf, unicodes=u(0x633,0x627))
      shaper = Shaper(self.ff, bbf)
      shaper.execute(buf)
      self.assertIsInstance(shaper.complexshaper, ArabicShaper)
      self.assertEqual(buf.serialize("arabic_joining", position=False), "uni0633.init(init)|uni0627.fina(fina)")

    def test_joining_2(self):
      bbf = Babelfont.open(self.fontfile)
      buf = Buffer(bbf, unicodes=u(0x633,0x633,0x627))
      shaper = Shaper(self.ff, bbf)
      shaper.execute(buf)
      self.assertIsInstance(shaper.complexshaper, ArabicShaper)
      self.assertEqual(buf.serialize("arabic_joining", position=False), "uni0633.init(init)|uni0633.medi(medi)|uni0627.fina(fina)")
