from dataclasses import dataclass
from fontFeatures import ValueRecord
from glyphtools import get_glyph_metrics, categorize_glyph
from fontFeatures.fontProxy import FontProxy
import unicodedata
from youseedee import ucd_data

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
class BufferItem:
    # codepoint: int
    # glyph: str
    # position: ValueRecord
    # category: str

    @classmethod
    def new_unicode(klass, codepoint):
        self = BufferItem()
        self.codepoint = codepoint
        self.glyph = None
        return self

    @classmethod
    def new_glyph(klass, glyph, font):
        self = BufferItem()
        self.glyph = glyph
        self.prep_glyph(font)
        return self

    def map_to_glyph(self, font):
        if not self.glyph:
            self.glyph = font.map_unicode_to_glyph(self.codepoint)
        self.prep_glyph(font)

    def prep_glyph(self, font):
        self.position = ValueRecord(xAdvance=get_glyph_metrics(font.font, self.glyph)["width"],)
        self.recategorize(font)

    def recategorize(self, font):
        self.category = categorize_glyph(font.font, self.glyph)

    def add_position(self, vr2):
        _add_value_records(self.position, vr2)


class Buffer:
    def __init__(self, font, glyphs=[], unicodes=[], direction=None, script=None, language=None):
        if not isinstance(font, FontProxy):
            font = FontProxy(font)
        self.font = font
        self.direction = direction
        self.script = script
        self.language = language
        self.fallback_mark_positioning = False
        self.fallback_glyph_classes = False
        self.items = []
        if glyphs:
            self.items = [BufferItem.new_glyph(g, font) for g in glyphs]
            self.clear_mask()
        elif unicodes:
            self.normalize(unicodes)
            self.guess_segment_properties()


    def normalize(self, unistring):
        self.items = [BufferItem.new_unicode(ord(char)) for char in unicodedata.normalize("NFC", unistring)]

    def guess_segment_properties(self):
        for u in self.items:
            # Guess segment properties
            if not self.script:
                thisScript = ucd_data(u.codepoint)["Script"]
                if thisScript not in ["Common", "Unknown", "Inherited"]:
                    self.script = thisScript
        if not self.direction:
            from fontFeatures.shaperLib.Shaper import _script_direction
            self.direction = _script_direction(self.script)

    def map_to_glyphs(self):
        glyphs = []
        for u in self.items:
            u.map_to_glyph(self.font)
        self.clear_mask()

    def __getitem__(self, key):
        indexed = self.mask[key]
        if isinstance(indexed, range) or isinstance(indexed, slice):
            indexed = slice(indexed.start, indexed.stop, indexed.step)
        if isinstance(indexed, list):
            return [self.items[g] for g in indexed]
        return self.items[indexed]

    def __setitem__(self, key, value):
        indexed = self.mask[key]
        if len(indexed) == 1:  # Easy
            self.items[indexed[0] : indexed[0] + 1] = value
            return
        if len(value) == 1:  # Also easy
            self.items[indexed[0]] = value[0]
            for i in reversed(indexed[1:]):
                del self.items[i]
            return
        else:
            raise ValueError("Too hard :-(")

    def __len__(self):
        return len(self.mask)

    def update(self):
        for g in self.items:
            g.recategorize(self.font)
        self.recompute_mask()

    def clear_mask(self):
        self.flags = 0
        self.markFilteringSet = None
        self.recompute_mask()

    def set_mask(self, flags, markFilteringSet=None):
        self.flags = flags
        self.markFilteringSet = markFilteringSet
        self.recompute_mask()

    def recompute_mask(self):
        mask = range(0, len(self.items))
        if self.flags & 0x2:  # IgnoreBases
            mask = list(filter(lambda ix: self.items[ix].category[0] != "base", mask))
        if self.flags & 0x4:  # IgnoreLigatures
            mask = list(
                filter(lambda ix: self.items[ix].category[0] != "ligature", mask)
            )
        if self.flags & 0x8:  # IgnoreMarks
            mask = list(filter(lambda ix: self.items[ix].category[0] != "mark", mask))
        if self.flags & 0x10:  # UseMarkFilteringSet
            mask = list(
                filter(
                    lambda ix: self.items[ix].category[0] != "mark"
                    or self.items[ix].items in self.markFilteringSet,
                    mask,
                )
            )
        self.mask = mask

    def serialize(self, additional = None, position=True):
        """Serialize a buffer to a string.

    Returns:
        The contents of the given buffer in a string format similar to
        that used by ``hb-shape``.

    """
        outs = []
        for info in self.items:
            if hasattr(info, "glyph"):
                outs.append("%s" % info.glyph)
            else:
                outs.append("%04x" % info.codepoint)
            if position and hasattr(info, "position"):
                position = info.position
                outs[-1] = outs[-1] + "+%i" % position.xAdvance
                if position.xPlacement != 0 or position.yPlacement != 0:
                    outs[-1] = outs[-1] + "@<%i,%i>" % (
                        position.xPlacement or 0,
                        position.yPlacement or 0,
                    )
            if additional and hasattr(info, additional):
                outs[-1] = outs[-1] + "(%s)" % getattr(info, additional)
        return "|".join(outs)
