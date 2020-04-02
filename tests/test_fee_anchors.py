from fontFeatures.feeLib import FeeParser
from fontTools.ttLib import TTFont

import unittest

class TestFeeAnchors(unittest.TestCase):
  p = FeeParser(TTFont("fonts/Roboto-Regular.ttf"))

  def test_parse_to_ff(self):
    self.p.parseString("""
      Anchors A {
        top <679 1600>
        bottom <691 0>
      };

      Anchors B {
        top <611 1612>
      };

      Anchors acutecomb { _top <-570 1290> };
      Anchors tildecomb { _top <-542 1256> };

      Feature mark { Attach &top &_top; };
""")

    self.assertEqual(self.p.fea.anchors["A"]["top"], (679,1600))
    self.assertEqual(self.p.fea.asFea(),"""
feature mark {
                        markClass acutecomb <anchor -570 129> @top;
            markClass tildecomb <anchor -542 125> @top;
            pos base A <anchor 679 1600> mark @top;
            pos base B <anchor 611 1612> mark @top;


} mark;
""")