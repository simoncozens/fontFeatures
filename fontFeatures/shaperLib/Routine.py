__all__ = ["apply_to_buffer"]


def apply_to_buffer(self, buf):
    buf.set_mask(self.flags, self.markFilteringSet)
    for r in self.rules:
        if r.apply_to_buffer(buf):
            return
