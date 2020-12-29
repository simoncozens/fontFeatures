from fontFeatures.shaperLib.Buffer import Buffer, BufferItem
from copy import copy
import unicodedata
from youseedee import ucd_data


def _is_default_ignorable(c):
    return (
        c in [0x00AD, 0x034F, 0x061C, 0x17B4, 0x17B5, 0xFEFF]
        or 0x180B <= c <= 0x180E
        or 0x200B <= c <= 0x200F
        or 0x202A <= c <= 0x202E
        or 0x2060 <= c <= 0x206F
        or 0xFE00 <= c <= 0xFE0F
        or 0xFFF0 <= c <= 0xFFF8
        or 0x1D173 <= c <= 0x1D17A
        or 0xE0000 <= c <= 0xE0FFF
    )


class BaseShaper:
    def __init__(self, plan, font, buf, features=[]):
        self.plan = plan
        self.font = font
        self.buffer = buf
        self.features = features

    def shape(self):
        # self.buffer.set_unicode_props()
        # self.insert_dotted_circles()
        # self.buffer.form_clusters()
        # self.buffer.ensure_native_direction()
        if not self.buffer.is_all_glyphs:
            self.preprocess_text()
            # Substitute pre
            self.substitute_default()
        self.substitute_complex()
        self.position()
        # Substitute post
        self.hide_default_ignorables()
        self.postprocess_glyphs()
        # self.buffer.propagate_flags()

    def preprocess_text(self):
        pass

    def postprocess_glyphs(self):
        pass

    def substitute_default(self):
        self.normalize_unicode_buffer()
        self.buffer.map_to_glyphs()
        self.plan.msg("Initial glyph mapping", self.buffer)
        # Setup masks
        # if self.buf.fallback_mark_positioning:
        # self.fallback_mark_position_recategorize_marks()
        pass

    def normalize_unicode_buffer(self):
        unistring = "".join([chr(item.codepoint) for item in self.buffer.items])
        self.buffer.store_unicode(unicodedata.normalize("NFC", unistring))

        # Some fix-ups from hb-ot-shape-normalize
        for item in self.buffer.items:
            if ucd_data(item.codepoint)[
                "General_Category"
            ] == "Zs" and self.font.glyphForCodepoint(0x20, False):
                item.codepoint = 0x20
                # Harfbuzz adjusts the width here, in _hb_ot_shape_fallback_spaces
            if item.codepoint == 0x2011 and self.font.glyphForCodepoint(0x2010, False):
                item.codepoint = 0x2010

    def collect_features(self, shaper):
        return []

    def substitute_complex(self):
        self._run_stage("sub")

    def position(self):
        self._run_stage("pos")
        # zero width default ignorables
        for i in range(0,len(self.buffer.items)):
            self.propagate_attachment_offsets(i)

    def propagate_attachment_offsets(self, i):
        if not hasattr(self.buffer.items[i], "attach_type"):
            return
        attach_type = self.buffer.items[i].attach_type
        attach_chain = self.buffer.items[i].attach_chain
        if not attach_chain:
            return
        self.buffer.items[i].attach_chain = None
        j = i + attach_chain
        if j >= len(self.buffer.items):
            return
        self.propagate_attachment_offsets(j)
        if attach_type == "cursive":
            self.buffer.items[i].position.yPlacement = (self.buffer.items[i].position.yPlacement or 0) + (self.buffer.items[j].position.yPlacement or 0) # XXX Horizontal only
        else:
            self.buffer.items[i].position.xPlacement += self.buffer.items[j].position.xPlacement or 0
            self.buffer.items[i].position.yPlacement += self.buffer.items[j].position.yPlacement or 0
            assert j < i
            if self.buffer.direction == "LTR":
                for k in range(j,i):
                    self.buffer.items[i].position.xPlacement -= self.buffer.items[k].position.xAdvance
                    self.buffer.items[i].position.yPlacement -= self.buffer.items[k].position.yAdvance or 0
            else:
                for k in range(j+1,i+1):
                    self.buffer.items[i].position.xPlacement += self.buffer.items[k].position.xAdvance
                    self.buffer.items[i].position.yPlacement += self.buffer.items[k].position.yAdvance or 0


    def _run_stage(self, current_stage):
        self.plan.msg("Running %s stage" % current_stage)
        for stage in self.plan.stages:
            lookups = []
            if isinstance(stage, list):  # Features
                for f in stage:
                    if f not in self.plan.fontfeatures.features:
                        continue
                    # XXX These should be ordered by ID
                    # XXX and filtered by language
                    lookups.extend(
                        [(routine, f) for routine in self.plan.fontfeatures.features[f]]
                    )
                self.plan.msg("Processing features: %s" % ",".join(stage))
                for r, feature in lookups:
                    self.plan.msg(
                        "Before %s (%s)" % (r.name, feature), buffer=self.buffer
                    )
                    r.apply_to_buffer(self.buffer, stage=current_stage, feature=feature)
                    self.plan.msg(
                        "After %s (%s)" % (r.name, feature), buffer=self.buffer
                    )
            else:
                # It's a pause. We only support GSUB pauses.
                if current_stage == "sub":
                    stage(current_stage)

    def hide_default_ignorables(self):
        space = BufferItem.new_unicode(0x20)
        space.map_to_glyph(self.buffer.font)
        if space.glyph == -1:
            return
        for ix, item in enumerate(self.buffer.items):
            if _is_default_ignorable(item.codepoint):
                item.glyph = space.glyph
                item.position.xAdvance = 0
                for i in self.buffer.items[ix:]:
                    if hasattr(i, "syllable_index"):
                        i.syllable_index += 1

    def would_substitute(self, feature, subbuffer_items):
        if not feature in self.plan.fontfeatures.features:
            return False
        subbuffer = Buffer(
            self.buffer.font,
            direction=self.buffer.direction,
            script=self.buffer.script,
            language=self.buffer.language,
        )
        subbuffer.clear_mask()
        subbuffer.items = [copy(x) for x in subbuffer_items]
        subbuffer.clear_mask()
        routines = self.plan.fontfeatures.features[feature]
        for r in routines:
            for rule in r.rules:
                if rule.stage == "pos":
                    continue
                if any(
                    [
                        rule.would_apply_at_position(subbuffer, i)
                        for i in range(len(subbuffer))
                    ]
                ):
                    return True
        return False
