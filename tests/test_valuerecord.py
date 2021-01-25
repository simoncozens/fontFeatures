from fontFeatures import ValueRecord
from babelfont.variablefont import VariableFont

import pytest

def test_variable_value_records():
  fontfile = "tests/data/SimpleTwoAxis.glyphs"
  vf = VariableFont(fontfile)
  vr = ValueRecord()
  vr.set_value_for_master(vf, "Regular", ValueRecord(0,0,0,0))
  vr.set_value_for_master(vf, "Bold", ValueRecord(0,0,100,0))

  vr.set_value_for_master(vf, "Regular Skewed", ValueRecord(0,10,0,0))
  vr.set_value_for_master(vf, "Bold Skewed", ValueRecord(0,20,150,0))

  semibold = vr.get_value_for_location(vf, {"Weight": 450, "Slant": 0 })
  assert semibold.xAdvance == 50

  book = vr.get_value_for_location(vf, {"Weight": 300, "Slant": 0 })
  assert book.xAdvance == 20

  regular_skewed = vr.get_value_for_location(vf, {"Weight": 200, "Slant": 10 })
  assert regular_skewed.xAdvance == 0
  assert regular_skewed.yPlacement == 10

  book_skewed = vr.get_value_for_location(vf, {"Weight": 300, "Slant": 10 })
  assert book_skewed.yPlacement == 12
  assert book_skewed.xAdvance == 30
