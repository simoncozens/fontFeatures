def shaper_inputs(self):
    return self.input


def _do_apply(self, buf, ix):
    from fontFeatures.jankyPOS.Buffer import BufferGlyph

    coverage = buf[ix : ix + len(self.input)]
    buf[ix : ix + len(self.input)] = [
        BufferGlyph(g, buf.font) for g in self.replacement
    ]
