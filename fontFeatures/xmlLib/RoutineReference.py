from lxml import etree


def toXML(self):
    root = etree.Element("routinereference")
    if self.name:
        root.attrib["name"] = self.name
    return root


@classmethod
def fromXML(klass, el):
    rule = klass(name=el.get("name"))
    id = el.get("id")
    return rule
