from glyphtools import categorize_glyph


def lookup_type(self):
    if self.is_cursive:
        return 3
    # Terrible hacks
    firstbase = list(self.bases.keys())[0]
    if hasattr(self, "fontfeatures") and self.fontfeatures.glyphclasses.get(firstbase) == "mark":
        return 6
    if self.font and categorize_glyph(self.font,firstbase)[0] == "mark":
        return 6
    return 4
