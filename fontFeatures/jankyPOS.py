from fontFeatures.ftUtils import get_glyph_metrics, categorize_glyph
from fontFeatures import ValueRecord, Attachment, Positioning, Chaining, Routine
import warnings


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


    def serialize_buffer(self, buf):
        """Returns the contents of the given buffer in a string format similar to
    that used by hb-shape."""
        outs = []
        for info in buf:
            position = info["position"]
            outs.append("%s" % info["glyph"])
            outs[-1] = outs[-1] + "+%i" % position.xAdvance
            if position.xPlacement != 0 or position.yPlacement != 0:
                outs[-1] = outs[-1] + "@<%i,%i>" % (position.xPlacement or 0, position.yPlacement or 0)
        return "|".join(outs)

    def positioning_buffer(self, glyphstring):
        return [
            { "glyph": g,
              "position": ValueRecord(xAdvance=get_glyph_metrics(self.font, g)["width"]),
              "category": categorize_glyph(self.font, g)
            }
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
        if self.direction == "RTL":
            buf = list(reversed(buf))
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
            g, vr = buf[i]["glyph"], buf[i]["position"]
            if rule.precontext or rule.postcontext:
                pre = [x["glyph"] for x in buf[i - len(rule.precontext) + 1 : i]]
                post = [x["glyph"] for x in buf[i + 1 : i + len(rule.postcontext) + 1]]
                if tuple(pre) != tuple(rule.precontext) or tuple(post) != tuple(
                    rule.postcontext
                ):
                    continue
            if g not in rule.glyphs[0]:
                continue
            add_value_records(vr, rule.valuerecords[0])
        return buf

    def attach(self, buf, rule):
        for ix, info in enumerate(buf):
            g = info["glyph"]
            vr = info["position"]
            if ix == 0:
                continue
            # XXX search backwards until you find a base
            # XXX Unless we are doing mkmk
            previous = ix - 1
            while previous > 0 and buf[previous]["category"][0] != "base":
                previous = previous - 1
            prev = buf[previous]["glyph"]
            prevVr = buf[previous]["position"]
            print("Trying %s(%i)/%s" % (g, ix, prev))
            if g in rule.marks and ix > 0 and prev in rule.bases:
                print("Attach %s -> %s" % ( g, prev))
                xpos = -(rule.bases[prev][0] - rule.marks[g][0])
                ypos = -(rule.bases[prev][1] - rule.marks[g][1])
                print(" %i, %i" % ( xpos, ypos))
                if rule.is_cursive:
                    xpos = xpos + (prevVr.xPlacement or 0)
                    ypos = ypos + (prevVr.yPlacement or 0)
                    prevVr.xPlacement = (prevVr.xPlacement or 0) + xpos - prevVr.xAdvance
                    prevVr.yPlacement = (prevVr.yPlacement or 0) + ypos
                else:
                    vr.xPlacement = (vr.xPlacement or 0) + xpos - prevVr.xAdvance
                    vr.yPlacement = (vr.yPlacement or 0) + ypos
        return buf
