def shaper_inputs(self):
    return self.input

def __find_masked_ix(buf, ix):
    # This probably could be done better...
    for i in range(len(buf.items)):
        if buf.mask[i] == ix: return i
    return -1

def _do_apply(self, buf, ix):
    # Save buffer mask
    flags = buf.flags
    markFilteringSet = buf.markFilteringSet
    old_unmasked_indexes = [ buf.mask[ix+i] for i in range(len(self.lookups)) if self.lookups[i] ]

    for i,lookups in enumerate(self.lookups):
        if not lookups:
            continue
        for routine in lookups:
            # Adjust mask and recompute index?
            unmasked_ix = old_unmasked_indexes[i]
            buf.set_mask(routine.flags, routine.markFilteringSet)
            newix = __find_masked_ix(buf, unmasked_ix)
            for rule in routine.rules:
                if rule._do_apply(buf, newix):
                    break

    buf.set_mask(flags, markFilteringSet)

