__all__ = ["apply_to_buffer"]


def glyphs_match(buffer_glyphs, routine_glyphs):
    if len(buffer_glyphs) != len(routine_glyphs):
        return False
    for a, b in zip(buffer_glyphs, routine_glyphs):
        if a.glyph not in b:
            return False
    return True


def apply_to_buffer(self, buf):
    applied = False
    coverage = self.shaper_inputs()
    coverage_l = len(coverage)
    if coverage_l < 1: return
    ix = 0
    if hasattr(self, "is_cursive") and self.is_cursive:
        coverage = list(reversed(coverage))
    # Watch for reversed application here
    while ix < len(buf) - coverage_l + 1:
        buffer_glyphs = buf[ix : ix + coverage_l]
        ix = ix + 1
        # Advancing index pointer here allows us to use
        # "continue" to drop out early, but it means that
        # following buffer computations look a bit funny.
        if not glyphs_match(buffer_glyphs, coverage):
            continue
        if hasattr(self, "precontext") and self.precontext:
            if ix < len(self.precontext):
                continue
            precontext = buf[ix - len(self.precontext) - 1 : ix - 1]
            if not glyphs_match(precontext, self.precontext):
                continue
        if hasattr(self, "postcontext") and self.postcontext:
            end_of_coverage = ix + coverage_l - 1
            if end_of_coverage + len(self.postcontext) > len(buf):
                continue
            postcontext = buf[end_of_coverage : end_of_coverage + len(self.postcontext)]
            if not glyphs_match(postcontext, self.postcontext):
                continue
        # We have a match
        self._do_apply(buf, ix - 1)
        buf.update()
        applied = True
    return applied
