from fontFeatures import Attachment, FontFeatures

import unittest

class TestAnchors(unittest.TestCase):
  def test_markbase(self):
    s = Attachment("top", "top_", {"A": (679,1600)}, {"acutecomb": (-570, 1290)})
    self.assertEqual(s.asFea(), "    pos base A <anchor 679 1600> mark @top;\n")
