def shaper_inputs(self):
    return [self.bases.keys(), self.marks.keys()]


def _do_apply_cursive(self, buf, ix):
    mark = buf[ix].glyph
    base = buf[ix + 1].glyph
    exit_x, exit_y = self.marks[mark]
    entry_x, entry_y = self.bases[base]
    d = exit_x + (buf[ix].position.xPlacement or 0)
    buf[ix].position.xAdvance = (buf[ix].position.xAdvance or 0) - d
    buf[ix].position.xPlacement = (buf[ix].position.xPlacement or 0) - d
    buf[ix+1].position.xAdvance = entry_x + (buf[ix + 1].position.xPlacement or 0)
    child = ix
    parent = ix + 1
    x_offset = entry_x - exit_x
    y_offset = entry_y - exit_y
    if True or not (self.flags & 1):  # LeftToRight XXX
        parent, child = child, parent
        x_offset = -x_offset
        y_offset = -y_offset
    buf[child].position.yPlacement = (buf[parent].position.yPlacement or 0) + y_offset


def _do_apply(self, buf, ix):
    if self.is_cursive:
        return _do_apply_cursive(self, buf, ix)
    from fontFeatures import ValueRecord
    mark = buf[ix].glyph
    base = buf[ix + 1].glyph
    xpos = self.bases[mark][0] - self.marks[base][0]
    ypos = self.bases[mark][1] - self.marks[base][1]
    vr = ValueRecord(xPlacement=xpos, yPlacement=ypos)
    if buf.direction == "LTR":
        vr.xPlacement = vr.xPlacement - buf[ix].position.xAdvance
    buf[ix + 1].add_position(vr)
