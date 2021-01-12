import logging
from fontFeatures import Rule


def shaper_inputs(self):
    return [self.bases.keys(), self.marks.keys()]

def find_base_backwards(self, buf, ix):
    start_ix = ix
    ix = ix - 1
    while ix >= 0:
        if buf[ix].glyph in self.bases.keys():
            # Check for unhelpful stuff in between
            my_category = buf[ix].category[0]
            for i in range(ix+1, start_ix):
                if buf[i].category[0] == my_category or buf[i].category[0] == "unknown":
                    # Oops, we skipped over another %s to get here
                    return None
            return ix
        ix = ix - 1
    return None

def would_apply_at_position(self, buf, ix, namedclasses={}):
    from fontFeatures.shaperLib.Rule import _expand_slot

    logging.getLogger("fontFeatures.shaperLib").debug("Testing if %s would apply at position %i" % (self.asFea(), ix))
    marks = _expand_slot(self.marks.keys(), namedclasses)
    bases = _expand_slot(self.bases.keys(), namedclasses)

    if self.is_cursive:
        if ix == 0:
            logging.getLogger("fontFeatures.shaperLib").debug(" * No, it has no adjacent glyph")
            return False
        if buf[ix].glyph in marks and buf[ix-1].glyph in bases:
            logging.getLogger("fontFeatures.shaperLib").debug(" * No, %s/%s is not a pair" % (buf[ix].glyph, buf[ix-1].glyph))
        logging.getLogger("fontFeatures.shaperLib").debug(" * Yes, %s/%s is a pair" % (buf[ix].glyph, buf[ix-1].glyph))
        return True



    # Mark to base is a bit different, as multiple marks can attach to a base
    # so we search backwards for the preceding base glyph
    # XXX mark to mark
    if buf[ix].glyph not in marks:
        logging.getLogger("fontFeatures.shaperLib").debug(" * No, %s is not in our mark list" % (buf[ix].glyph))
        return False
    base_ix = find_base_backwards(self, buf, ix)
    if base_ix is None:
        logging.getLogger("fontFeatures.shaperLib").debug(" * No, I couldn't find a base glyph")
        return False
    if buf[base_ix].glyph not in bases:
        logging.getLogger("fontFeatures.shaperLib").debug(" * No, %s is not in our base list" % buf[base_ix].glyph)
        return False
    logging.getLogger("fontFeatures.shaperLib").debug(" * Yes, attaching mark %s/%i to %s/%i" % (buf[ix].glyph, ix, buf[base_ix].glyph, base_ix))
    return True

def _do_apply_cursive(self, buf, ix):
    mark = buf[ix].glyph
    base = buf[ix - 1].glyph
    if mark not in self.marks or base not in self.bases:
        return
    exit_x, exit_y = self.marks.get(mark, (0,0))
    entry_x, entry_y = self.bases.get(base, (0,0))
    d = exit_x + (buf[ix-1].position.xPlacement or 0)
    buf[ix-1].position.xAdvance = (buf[ix-1].position.xAdvance or 0) - d
    buf[ix-1].position.xPlacement = (buf[ix-1].position.xPlacement or 0) - d
    buf[ix].position.xAdvance = entry_x + (buf[ix].position.xPlacement or 0)
    child = ix -1
    parent = ix
    x_offset = entry_x - exit_x
    y_offset = entry_y - exit_y
    if not (self.flags & 1):  # LeftToRight XXX
        parent, child = child, parent
        x_offset = -x_offset
        y_offset = -y_offset
    buf[child].position.xPlacement = x_offset
    buf[ix].attach_type = "cursive"
    buf[ix].attach_chain = parent - child


def _do_apply(self, buf, ix, namedclasses={}):
    if self.is_cursive:
        return _do_apply_cursive(self, buf, ix)
    from fontFeatures import ValueRecord
    base_ix = find_base_backwards(self, buf, ix)
    mark = buf[ix].glyph
    base = buf[base_ix].glyph
    xpos = self.bases[base][0] - self.marks[mark][0]
    ypos = self.bases[base][1] - self.marks[mark][1]
    buf[ix].position.xPlacement = xpos
    buf[ix].position.yPlacement = ypos
    buf[ix].attach_type = "mark"
    buf[ix].attach_chain = base_ix - ix
