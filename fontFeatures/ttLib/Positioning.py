def lookup_type(self):
    if (not self.precontext or len(self.precontext) == 0) and (
        not self.postcontext or len(self.postcontext) == 0
    ):
        if len(self.glyphs) == 1:
            return 1
        if len(self.glyphs) == 2:
            return 2
    else:
    		if len(self.glyphs) == 1:
	    			return 1
    return 8  # ???
