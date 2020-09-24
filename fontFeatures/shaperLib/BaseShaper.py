class BaseShaper():
  def __init__(self, plan, fontproxy, buf, features = []):
    self.plan = plan
    self.fontproxy = fontproxy
    self.buffer = buf
    self.features = features

  def shape(self):
    # self.buffer.set_unicode_props()
    # self.buffer.insert_dotted_circle(self.font)
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
    self.buffer.map_to_glyphs()
    # Setup masks
    # if self.buf.fallback_mark_positioning:
      # self.fallback_mark_position_recategorize_marks()
    pass

  def collect_features(self, shaper):
    return []

  def substitute_complex(self):
    self._run_stage("sub")

  def position(self):
    self._run_stage("pos")

  def _run_stage(self, current_stage):
    for stage in self.plan.stages:
        lookups = []
        if isinstance(stage, list): # Features
            for f in stage:
                if f not in self.plan.fontfeatures.features:
                    continue
                # XXX These should be ordered by ID
                lookups.extend(self.plan.fontfeatures.features[f])
            for r in lookups:
                r.apply_to_buffer(self.buffer, current_stage)
        else:
            # It's a pause
            stage(current_stage)

  def hide_default_ignorables(self):
    pass
