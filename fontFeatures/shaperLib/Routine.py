__all__ = ["apply_to_buffer"]


def apply_to_buffer(self, buf, stage=None, feature=None):
    buf.set_mask(self.flags, self.markFilteringSet)
    if feature:
        buf.set_feature_mask(feature)

    for r in self.rules:
        if stage and r.stage != stage:
            continue
        if r.apply_to_buffer(buf):
            return
