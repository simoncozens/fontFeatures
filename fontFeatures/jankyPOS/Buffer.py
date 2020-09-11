from dataclasses import dataclass
from fontFeatures import ValueRecord
from glyphtools import get_glyph_metrics, categorize_glyph


def _add_value_records(vr1, vr2):
    if vr1.xPlacement or vr2.xPlacement:
        vr1.xPlacement = (vr1.xPlacement or 0) + (vr2.xPlacement or 0)
    if vr1.yPlacement or vr2.yPlacement:
        vr1.yPlacement = (vr1.yPlacement or 0) + (vr2.yPlacement or 0)
    if vr1.xAdvance or vr2.xAdvance:
        vr1.xAdvance = (vr1.xAdvance or 0) + (vr2.xAdvance or 0)
    if vr1.yAdvance or vr2.yAdvance:
        vr1.yAdvance = (vr1.yAdvance or 0) + (vr2.yAdvance or 0)


@dataclass
class BufferGlyph:
    glyph: str
    position: ValueRecord
    category: str

    def __init__(self, glyph, font):
        self.glyph = glyph
        self.position = ValueRecord(xAdvance=get_glyph_metrics(font, glyph)["width"],)
        self.recategorize(font)

    def recategorize(self, font):
        self.category = categorize_glyph(font, self.glyph)

    def add_position(self, vr2):
        _add_value_records(self.position, vr2)


class Buffer:
    def __init__(self, glyphstring, font):
        self.font = font
        self.glyphs = [BufferGlyph(g, font) for g in glyphstring]
        self.clear_mask()

    def __getitem__(self, key):
        indexed = self.mask[key]
        if isinstance(indexed, range) or isinstance(indexed, slice):
            indexed = slice(indexed.start, indexed.stop, indexed.step)
        if isinstance(indexed, list):
            return [self.glyphs[g] for g in indexed]
        return self.glyphs[indexed]

    def __setitem__(self, key, value):
        indexed = self.mask[key]
        if len(indexed) == 1:  # Easy
            self.glyphs[indexed[0] : indexed[0] + 1] = value
            return
        if len(value) == 1:  # Also easy
            self.glyphs[indexed[0]] = value[0]
            for i in reversed(indexed[1:]):
                del self.glyphs[i]
            return
        else:
            raise ValueError("Too hard :-(")

    def __len__(self):
        return len(self.mask)

    def update(self):
        for g in self.glyphs:
            g.recategorize(self.font)
        self.recompute_mask()

    def clear_mask(self):
        self.flags = 0
        self.recompute_mask()

    def set_mask(self, flags, markFilteringSet=None):
        self.flags = flags
        self.markFilteringSet = markFilteringSet
        self.recompute_mask()

    def recompute_mask(self):
        mask = range(0, len(self.glyphs))
        if self.flags & 0x2:  # IgnoreBases
            mask = list(filter(lambda ix: self.glyphs[ix].category[0] != "base", mask))
        if self.flags & 0x4:  # IgnoreLigatures
            mask = list(
                filter(lambda ix: self.glyphs[ix].category[0] != "ligature", mask)
            )
        if self.flags & 0x8:  # IgnoreMarks
            mask = list(filter(lambda ix: self.glyphs[ix].category[0] != "mark", mask))
        if self.flags & 0x10:  # UseMarkFilteringSet
            mask = list(
                filter(
                    lambda ix: self.glyphs[ix].category[0] != "mark"
                    or self.glyphs[ix].glyphs in self.markFilteringSet,
                    mask,
                )
            )
        self.mask = mask

    def serialize(self):
        """Serialize a buffer to a string.

    Returns:
        The contents of the given buffer in a string format similar to
        that used by ``hb-shape``.

    """
        outs = []
        for info in self.glyphs:
            position = info.position
            outs.append("%s" % info.glyph)
            outs[-1] = outs[-1] + "+%i" % position.xAdvance
            if position.xPlacement != 0 or position.yPlacement != 0:
                outs[-1] = outs[-1] + "@<%i,%i>" % (
                    position.xPlacement or 0,
                    position.yPlacement or 0,
                )
        return "|".join(outs)
