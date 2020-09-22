from glyphtools import isglyphs

class FontProxy:
	def __init__(self, font):
		self.isglyphs = isglyphs(font)
		self.font = font
		if self.isglyphs:
			self.setup_glyphs()
		else:
			self.setup_tt()

	def setup_glyphs(self):
		self.glyphs = list(sorted([x.name for x in self.font.font.glyphs]))

	def setup_tt(self):
		self.glyphs = list(sorted(self.font.getGlyphOrder()))

