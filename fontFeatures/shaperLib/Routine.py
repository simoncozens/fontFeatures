import logging

__all__ = ["apply_to_buffer"]


def apply_to_buffer(self, buf, stage=None, feature=None, namedclasses={}):
    buf.set_mask(self.flags, self.markFilteringSet, self.markAttachmentSet)
    if feature:
        buf.set_feature_mask(feature)
    i = 0
    while i < len(buf): # (which may change!)
        for r in self.rules:
            if stage and r.stage != stage:
                continue
            buf.set_mask(r.flags, self.markFilteringSet, self.markAttachmentSet)
            if r.would_apply_at_position(buf, i,namedclasses=namedclasses):
                logging.getLogger("fontFeatures.shaperLib").debug("Applying rule %s at position %i\n" % (r.asFea(), i))
                delta = r._do_apply(buf, i, namedclasses=namedclasses)
                buf.update()
                if delta:
                    i = i + delta
                break
        i = i + 1
