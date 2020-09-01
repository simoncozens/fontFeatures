"""
JankyPOS
========

JankyPOS is a glyph string positioning tool. It's janky because it
implements half of what an OpenType shaping engine ought to do, badly.
This is reasonable in this situation, because it's not aiming to be a
full shaping engine, but to have just enough logic to run the rules in
a font and work out where the glyphs are likely to end up.

FontFeatures plugin modules can use JankyPOS to position glyph strings
that they enumerate and determine whether further action needs to be
taken based on the computed positions. (For instance, if the rules so
far lead to collisions or clashes.)
"""

from glyphtools import get_glyph_metrics, categorize_glyph
from fontFeatures import ValueRecord, Attachment, Positioning, Chaining, Routine
import warnings

def _add_value_records(vr1, vr2):
    if vr1.xPlacement or vr2.xPlacement:
        vr1.xPlacement = (vr1.xPlacement or 0) + (vr2.xPlacement or 0)
    if vr1.yPlacement or vr2.yPlacement:
        vr1.yPlacement = (vr1.yPlacement or 0) + (vr2.yPlacement or 0)
    if vr1.xAdvance or vr2.xAdvance:
        vr1.xAdvance = (vr1.xAdvance or 0) + (vr2.xAdvance or 0)
    if vr1.yAdvance or vr2.yAdvance:
        vr1.yAdvance = (vr1.yAdvance or 0) + (vr2.yAdvance or 0)


class JankyPos:
    """Initialize a positioner with a font.

    Args:
        font: A fontTools ``TTFont`` object.
        direction: Text direction. Either "LTR" or "RTL".
    """
    def __init__(self, font, direction="LTR"):
        self.font = font
        self.direction = direction

    def positioning_buffer(self, glyphstring):
        """Create a positioning buffer.

        Args:
            glyphstring: A sequence of glyph names.

        Returns:
            An array of positioning information, to be passed to
            positioning methods.
        """
        return [
            {
                "glyph": g,
                "position": ValueRecord(
                    xAdvance=get_glyph_metrics(self.font, g)["width"],
                ),
                "category": categorize_glyph(self.font, g),
            }
            for g in glyphstring
        ]

    def serialize_buffer(self, buf):
        """Serialize a buffer to a string.

        Args:
            buf: A buffer returned from :py:meth:`positioning_buffer`.

        Returns:
            The contents of the given buffer in a string format similar to
            that used by ``hb-shape``.

        """
        outs = []
        for info in buf:
            position = info["position"]
            outs.append("%s" % info["glyph"])
            outs[-1] = outs[-1] + "+%i" % position.xAdvance
            if position.xPlacement != 0 or position.yPlacement != 0:
                outs[-1] = outs[-1] + "@<%i,%i>" % (
                    position.xPlacement or 0,
                    position.yPlacement or 0,
                )
        return "|".join(outs)

    def process_fontfeatures(self, buf, ff):
        """Position a buffer based on the rules of a fontFeatures object.

        This applies the features in order defined in Harfbuzz's "default
        shaper" implementation. Note that this may not be sufficient for
        Indic scripts.

        Args:
            buf: A buffer returned from :py:meth:`positioning_buffer`.
            ff: A fontFeatures object.

        Returns:
            The buffer, but with positioning information.
        """
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
        """Apply a set of rules to a buffer.

        This applies rules directly to the buffer.

        Args:
            buf: A buffer returned from :py:meth:`positioning_buffer`.
            rules: A sequence of fontFeatures rules (Positioning, Attachment
                or Chaining.)

        Returns:
            The buffer, but with positioning information.
        """
        for r in rules:
            if isinstance(r, Positioning):
                if len(r.glyphs) == 1:
                    buf = self._position_one(buf, r)
                else:
                    continue  # XXX
            elif isinstance(r, Attachment):
                if r.is_cursive:
                    buf = self._attach_cursive(buf, r)
                else:
                    buf = self._attach(buf, r)
            elif isinstance(r, Chaining):
                buf = self._chain(buf, r)
            else:
                continue
        return buf

    def _chain(self, buf, rule):
        # XXXX
        return buf

    def _position_one(self, buf, rule):
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
            _add_value_records(vr, rule.valuerecords[0])
        return buf

    def _attach(self, buf, rule):
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
            if g in rule.marks and ix > 0 and prev in rule.bases:
                xpos = rule.bases[prev][0] - rule.marks[g][0]
                ypos = rule.bases[prev][1] - rule.marks[g][1]
                vr.xPlacement = (vr.xPlacement or 0) + xpos
                vr.yPlacement = (vr.yPlacement or 0) + ypos
                if self.direction == "LTR":
                    vr.xPlacement = (vr.xPlacement or 0) - prevVr.xAdvance
        return buf

    def _attach_cursive(self, buf, rule):
        for j, info in enumerate(buf):
            g = info["glyph"]
            vr = info["position"]
            if j == 0 or buf[j]["category"][0] != "base":
                continue
            i = j - 1
            while i > 0 and buf[i]["category"][0] != "base":
                i = i - 1

            # Get entry anchor for i and exit anchor for i
            prev = buf[i]["glyph"]
            if g not in rule.bases or not prev in rule.marks:
                continue
            exit_x, exit_y = rule.marks[prev]
            entry_x, entry_y = rule.bases[g]
            if self.direction == "RTL":
                d = exit_x + (buf[i]["position"].xPlacement or 0)
                buf[i]["position"].xAdvance = (buf[i]["position"].xAdvance or 0) - d
                buf[i]["position"].xPlacement = (buf[i]["position"].xPlacement or 0) - d
                buf[j]["position"].xAdvance = entry_x + (
                    buf[j]["position"].xPlacement or 0
                )
            else:
                raise ValueError
            child = i
            parent = j
            x_offset = entry_x - exit_x
            y_offset = entry_y - exit_y
            if True or not (rule.flags & 1):  # LeftToRight XXX
                parent, child = child, parent
                x_offset = -x_offset
                y_offset = -y_offset
            buf[child]["position"].yPlacement = (
                buf[parent]["position"].yPlacement or 0
            ) + y_offset
        return buf


if __name__ == "__main__":
    import sys
    from fontFeatures.ttLib import unparse
    from fontTools.ttLib import TTFont
    import argparse

    parser = argparse.ArgumentParser(description="Test janky positioning")
    parser.add_argument("font", metavar="FONT", help="font file")
    parser.add_argument("glyphs", metavar="GLYPHS", help="glyph string")
    parser.add_argument("--direction", action="store", help="direction")

    args = parser.parse_args()
    font = TTFont(args.font)
    glyphs = args.glyphs.split()
    ff = unparse(font)
    janky = JankyPos(font)
    if args.direction:
        janky.direction = args.direction
    buf = janky.positioning_buffer(glyphs)
    buf = janky.process_fontfeatures(buf, ff)
    print(janky.serialize_buffer(buf))
