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

      Anchors acutecomb {
        _top <-570 1290>
      };

      Anchors circumflexcomb {
        _top <-591 1290>
      };

      Feature mark { Attach &top &_top; };
""")

    self.assertEqual(self.p.fea.anchors["A"]["top"], (679,1600))
    print(self.p.fea.asFea())