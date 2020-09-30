from glyphtools import isglyphs
from fontTools.ttLib import TTFont


class FontProxy:
    def __init__(self, font):
        self.isglyphs = not isinstance(font, TTFont) and isglyphs(font)
        self.font = font
        if self.isglyphs:
            self.setup_glyphs()
        else:
            self.setup_tt()

    @classmethod
    def opener(klass, fontfile):
        if fontfile.endswith(".otf") or fontfile.endswith(".ttf"):
            font = TTFont(fontfile)
            return FontProxy(font)
        if fontfile.endswith(".glyphs"):
            import glyphsLib

            return FontProxy(glyphsLib.GSFont(fontfile).masters[0])

    def setup_glyphs(self):
        list(sorted([x.name for x in self.font.font.glyphs]))
        self.mapping = {}
        self.glyphs = []
        self.reverseMapping = {}
        for x in self.font.font.glyphs:
            self.glyphs.append(x.name)
            self.reverseMapping[x.name] = []
            for u in x.unicodes:
                self.mapping[int(u, 16)] = x.name
                self.reverseMapping[x.name].append(int(u, 16))

    def setup_tt(self):
        self.glyphs = list(sorted(self.font.getGlyphOrder()))
        self.mapping = self.font["cmap"].getBestCmap()
        self.reverseMapping = self.font["cmap"].buildReversed()

    def map_unicode_to_glyph(self, u):
        if not u in self.mapping:
            if ".notdef" in self.glyphs:
                return ".notdef"
            return None
        return self.mapping[u]

    def map_glyph_to_unicode(self, glyph):
        if glyph not in self.reverseMapping:
            return None
        options = list(self.reverseMapping[glyph])
        if options:
            return options[0]
        return None
