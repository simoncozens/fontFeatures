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

	def setup_glyphs(self):
		list(sorted([x.name for x in self.font.font.glyphs]))
		self.mapping = {}
		self.glyphs = []
		for x in self.font.font.glyphs:
			self.glyphs.append(x.name)
			for u in x.unicodes:
				self.mapping[int(u,16)] = x.name

	def setup_tt(self):
		self.glyphs = list(sorted(self.font.getGlyphOrder()))
		self.mapping = self.font["cmap"].getBestCmap()

	def map_unicode_to_glyph(self, u):
		if not u in self.mapping:
			if ".notdef" in self.glyphs:
				return ".notdef"
			return None
		return self.mapping[u]

