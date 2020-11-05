from fontFeatures.shaperLib.Buffer import Buffer
from copy import copy
import unicodedata


class BaseShaper():
  def __init__(self, plan, font, buf, features = []):
    self.plan = plan
    self.font = font
    self.buffer = buf
    self.features = features

  def shape(self):
    # self.buffer.set_unicode_props()
    # self.insert_dotted_circles()
    # self.buffer.form_clusters()
    # self.buffer.ensure_native_direction()
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

  def collect_features(self, shaper):
    return []

  def substitute_complex(self):
    self._run_stage("sub")

  def position(self):
    self._run_stage("pos")

  def _run_stage(self, current_stage):
    self.plan.msg("Running %s stage" % current_stage)
    for stage in self.plan.stages:
        lookups = []
        if isinstance(stage, list): # Features
            for f in stage:
                if f not in self.plan.fontfeatures.features:
                    continue
                # XXX These should be ordered by ID
                lookups.extend(
                    [(routine, f) for routine in self.plan.fontfeatures.features[f]]
                )
            self.plan.msg("Processing features: %s" % ",".join(stage))
            for r, feature in lookups:
                self.plan.msg("Before %s (%s)" % (r.name, feature), buffer=self.buffer)
                r.apply_to_buffer(self.buffer, stage=current_stage, feature=feature)
                self.plan.msg("After %s (%s)" % (r.name, feature), buffer=self.buffer)
        else:
            # It's a pause. We only support GSUB pauses.
            if current_stage == "sub":
                stage(current_stage)

  def hide_default_ignorables(self):
    pass

  def would_substitute(self, feature, subbuffer_items):
    if not feature in self.plan.fontfeatures.features:
        return False
    subbuffer = Buffer(self.buffer.font, direction=self.buffer.direction, script=self.buffer.script, language=self.buffer.language)
    subbuffer.clear_mask()
    subbuffer.items = [copy(x) for x in subbuffer]
    subbuffer.clear_mask()
    routines = self.plan.fontfeatures.features[feature]
    for r in routines:
        for rule in r.rules:
            if rule.stage == "pos":
                continue
            if rule.apply_to_buffer(subbuffer):
                return True
    return False
