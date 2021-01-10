from lxml import etree


def toXML(self):
    root = etree.Element("routinereference")
    if self.name:
        root.attrib["name"] = self.name
    if self.id is not None:
        root.attrib["id"] = str(self.id)
    return root


@classmethod
def fromXML(klass, el):
    from fontFeatures import RoutineReference

    rule = klass(
        address=[el.get("address")], name=el.get("name"), flags=(int(el.get("flags") or 0))
    )
    for r in el:
        rule.addRule(Rule.fromXML(r))
    return rule
