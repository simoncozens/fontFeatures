import logging

__all__ = ["apply_to_buffer", "would_apply_at_position", "pre_post_context_matches"]


def i2s(buffer_items):
    return "|".join([x.glyph for x in buffer_items])

def glyphs_match(buffer_glyphs, routine_glyphs):
    if len(buffer_glyphs) != len(routine_glyphs):
        return False
    for a, b in zip(buffer_glyphs, routine_glyphs):
        if a.glyph not in b:
            return False
    return True

def pre_post_context_matches(self, buf, ix):
    if hasattr(self, "precontext") and self.precontext:
        if ix < len(self.precontext):
            logging.getLogger("fontFeatures.shaperLib").debug(" - No, not enough precontext")
            return False
        precontext = buf[ix - len(self.precontext) : ix]
        if not glyphs_match(precontext, self.precontext):
            logging.getLogger("fontFeatures.shaperLib").debug(" - No, precontext doesn't match %s != %s" % (i2s(precontext), self.precontext))
            return False
    if hasattr(self, "postcontext") and self.postcontext:
        coverage = self.shaper_inputs()
        coverage_l = len(coverage)
        end_of_coverage = ix + coverage_l
        if end_of_coverage + len(self.postcontext) > len(buf):
            logging.getLogger("fontFeatures.shaperLib").debug(" - No, not enough postcontext")
            return False
        postcontext = buf[end_of_coverage : end_of_coverage + len(self.postcontext)]
        if not glyphs_match(postcontext, self.postcontext):
            logging.getLogger("fontFeatures.shaperLib").debug(" - No, postcontext doesn't match %s != %s" % (i2s(postcontext), self.postcontext))
            return False
    return True

def would_apply_at_position(self, buf, ix):
    logging.getLogger("fontFeatures.shaperLib").debug("Testing if %s would apply at position %i" % (self.asFea(), ix))
    coverage = self.shaper_inputs()
    coverage_l = len(coverage)
    if coverage_l < 1: return False
    buffer_glyphs = buf[ix : ix + coverage_l]

    if not glyphs_match(buffer_glyphs, coverage):
        logging.getLogger("fontFeatures.shaperLib").debug(" - No! %s != %s" % (i2s(buffer_glyphs), coverage))
        return False

    if not pre_post_context_matches(self, buf, ix):
        return False

    logging.getLogger("fontFeatures.shaperLib").debug(" - Yes! %s == %s" % (i2s(buffer_glyphs), coverage))
    return True

