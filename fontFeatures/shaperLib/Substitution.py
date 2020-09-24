def shaper_inputs(self):
    return self.input


def _do_apply(self, buf, ix):
    from fontFeatures.jankyPOS.Buffer import BufferItem

    coverage = buf[ix : ix + len(self.input)]
    buf[ix : ix + len(self.input)] = [
        BufferItem.new_glyph(g, buf.font) for g in self.replacement
    ]
