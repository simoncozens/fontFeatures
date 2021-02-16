def lookup_type(self):
    if not self.has_context:
        if len(self.glyphs) == 1:
            return 1
        if len(self.glyphs) == 2:
            return 2
    return 7

