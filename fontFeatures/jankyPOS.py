from fontFeatures.ftUtils import get_glyph_metrics
from fontFeatures import ValueRecord, Attachment, Positioning, Chaining

def add_value_records(vr1, vr2):
  if vr1.xPlacement or vr2.xPlacement: vr1.xPlacement = (vr1.xPlacement or 0) + (vr2.xPlacement or 0)
  if vr1.yPlacement or vr2.yPlacement: vr1.yPlacement = (vr1.yPlacement or 0) + (vr2.yPlacement or 0)
  if vr1.xAdvance or vr2.xAdvance: vr1.xAdvance = (vr1.xAdvance or 0) + (vr2.xAdvance or 0)
  if vr1.yAdvance or vr2.yAdvance: vr1.yAdvance = (vr1.yAdvance or 0) + (vr2.yAdvance or 0)

class JankyPos:
  def __init__(self, font):
    self.font = font

  def positioning_buffer(self, glyphstring, direction="LTR"):
    if direction == "RTL": glyphstring = list(reversed(glyphstring))
    return [(g,
              ValueRecord(
                xAdvance = get_glyph_metrics(self.font,g)["width"]
              )
            ) for g in glyphstring]

  def process_rules(self, buf, rules):
    for r in rules:
      if isinstance(r, Positioning):
        if len(r.glyphs) == 1:
          buf = self.position_one(buf, r)
        else:
          raise ValueError
      elif isinstance(r, Attachment):
        buf = self.attach(buf, r)
      elif isinstance(r, Chaining):
        buf = self.chain(buf, r)
      else:
        raise ValueError()
    return buf

  def position_one(self, buf, rule):
    applicable_range = range(0 + len(rule.precontext), len(buf) - len(rule.postcontext))
    assert(len(rule.glyphs) == 1)
    for i in applicable_range:
      g, vr = buf[i]
      if rule.precontext or rule.postcontext:
        pre = [x[0] for x in buf[i-len(precontext)+1:i]]
        post = [x[0] for x in buf[i+1:i+len(postcontext)+1]]
        import code; code.interact(local=locals())
        if tuple(pre) != tuple(rule.precontext) or tuple(post) != tuple(rule.postcontext):
          continue
      if not g in rule.glyphs[0]: continue
      add_value_records(vr, rule.valuerecords[0])
    return buf

  def attach(self, buf, rule):
    for ix, (g,vr) in enumerate(buf):
      if ix == 0: continue
      # XXX search backwards until you find a base
      prev = buf[ix-1][0]
      if g in rule.marks and ix>0 and prev in rule.bases:
        xpos = rule.bases[prev][0] - rule.marks[g][0]
        ypos = rule.bases[prev][1] - rule.marks[g][1]
        vr.xPlacement = (vr.xPlacement or 0) + xpos - buf[ix-1][1].xAdvance
        vr.yPlacement = (vr.yPlacement or 0) + ypos
    return buf

