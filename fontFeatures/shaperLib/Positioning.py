def shaper_inputs(self):
    return self.glyphs


def _do_apply(self, buf, ix):
    coverage = buf[ix : ix + len(self.glyphs)]
    for glyph, vr in zip(coverage, self.valuerecords):
    	glyph.add_position(vr)
