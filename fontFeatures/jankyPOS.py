from fontFeatures.ftUtils import get_glyph_metrics
from fontFeatures import ValueRecord, Attachment, Positioning, Chaining, Routine


def add_value_records(vr1, vr2):
    if vr1.xPlacement or vr2.xPlacement:
        vr1.xPlacement = (vr1.xPlacement or 0) + (vr2.xPlacement or 0)
    if vr1.yPlacement or vr2.yPlacement:
        vr1.yPlacement = (vr1.yPlacement or 0) + (vr2.yPlacement or 0)
    if vr1.xAdvance or vr2.xAdvance:
        vr1.xAdvance = (vr1.xAdvance or 0) + (vr2.xAdvance or 0)
    if vr1.yAdvance or vr2.yAdvance:
        vr1.yAdvance = (vr1.yAdvance or 0) + (vr2.yAdvance or 0)


class JankyPos:
    def __init__(self, font, direction="LTR"):
        self.font = font
        self.direction = direction

    def positioning_buffer(self, glyphstring):
        if self.direction == "RTL":
            glyphstring = list(reversed(glyphstring))
        return [
            (g, ValueRecord(xAdvance=get_glyph_metrics(self.font, g)["width"]))
            for g in glyphstring
        ]

    def process_fontfeatures(self, buf, ff):
        features = ["rvrn"]
        if self.direction == "LTR":
            features.extend(["ltra", "ltrm"])
        elif self.direction == "RTL":
            features.extend(["rtla", "rtlm"])
        features.extend(["frac", "numr", "dnom", "rand"])
        features.extend(["abvm", "blwm", "ccmp", "locl", "mark", "mkmk", "rlig"])
        if self.direction == "LTR" or self.direction == "RTL":
            features.extend(["calt", "clig", "curs", "dist", "kern", "liga", "rclt"])
        else:
            features.extend(["vert"])

        for f in features:
            if f not in ff.features:
                continue
            for r in ff.features[f]:
                if isinstance(r, Routine):
                    buf = self.process_rules(buf, r.rules)
                else:
                    buf = self.process_rules(buf, [r])
        return buf

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
                continue
        return buf

    def position_one(self, buf, rule):
        applicable_range = range(
            0 + len(rule.precontext), len(buf) - len(rule.postcontext)
        )
        assert len(rule.glyphs) == 1
        for i in applicable_range:
            g, vr = buf[i]
            if rule.precontext or rule.postcontext:
                pre = [x[0] for x in buf[i - len(rule.precontext) + 1 : i]]
                post = [x[0] for x in buf[i + 1 : i + len(rule.postcontext) + 1]]
                if tuple(pre) != tuple(rule.precontext) or tuple(post) != tuple(
                    rule.postcontext
                ):
                    continue
            if g not in rule.glyphs[0]:
                continue
            add_value_records(vr, rule.valuerecords[0])
        return buf

    def attach(self, buf, rule):
        for ix, (g, vr) in enumerate(buf):
            if ix == 0:
                continue
            # XXX search backwards until you find a base
            prev = buf[ix - 1][0]
            if g in rule.marks and ix > 0 and prev in rule.bases:
                prevVr = buf[ix - 1][1]
                xpos = rule.bases[prev][0] - rule.marks[g][0]
                ypos = rule.bases[prev][1] - rule.marks[g][1]
                if rule.is_cursive:
                    xpos = xpos + (prevVr.xPlacement or 0)
                    ypos = ypos + (prevVr.yPlacement or 0)
                vr.xPlacement = (vr.xPlacement or 0) + xpos - prevVr.xAdvance
                vr.yPlacement = (vr.yPlacement or 0) + ypos
        return buf
