def lookup_type(self):
    if self.reverse:
        return 8
    if len(self.lookups) > 0 and any([x is not None for x in self.lookups]):
        return 6  # Chaining
    # if self.input == self.replacement: # It's an ignore
    # return 6
    if len(self.input) == 1 and len(self.replacement) == 1:
        if len(self.input[0]) == 1 and len(self.replacement[0]) > 1:
            return 3  # Alternate
        else:
            return 1  # Single
    if len(self.input) > 1 and len(self.replacement) == 1:
        return 4  # Ligature

    if len(self.input) > 1 and len(self.replacement) > 1:
        return 9  # Not directly expressible!

    if len(self.replacement) > 1:
        return 2
