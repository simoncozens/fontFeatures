from lxml import etree


def _toXML(self, root):
    root.set("basename", self.base_name)
    root.set("markname", self.mark_name)
    for n, anchor in self.bases.items():
        base = etree.SubElement(root, "base")
        base.set("name", n)
        base.set("anchorX", str(anchor[0]))
        base.set("anchorY", str(anchor[1]))
    for n, anchor in self.marks.items():
        mark = etree.SubElement(root, "mark")
        mark.set("name", n)
        mark.set("anchorX", str(anchor[0]))
        mark.set("anchorY", str(anchor[1]))
    return root


@classmethod
def fromXML(klass, el):
    import code; code.interact(local=locals())
    rule = klass(
        klass._slotArray(klass, el.find("glyphs")),
        positions,
        precontext=klass._slotArray(klass, el.find("precontext")),
        postcontext=klass._slotArray(klass, el.find("postcontext")),
        address=el.get("address"),
        languages=el.get("languages"),
        flags=el.get("flags"),
    )
    return rule
