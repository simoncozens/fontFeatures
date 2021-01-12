from lxml import etree


def toXML(self):
    root = etree.Element("routine")
    if self.flags:
        root.attrib["flags"] = str(self.flags)
    if self.address:
        root.attrib["address"] = str("|".join(self.address))
    if self.name:
        root.attrib["name"] = self.name
    for r in self.rules:
        root.append(r.toXML())

    return root


@classmethod
def fromXML(klass, el):
    from fontFeatures import Rule

    rule = klass(
        address=(el.get("address") or "").split("|"), name=el.get("name"), flags=(int(el.get("flags") or 0))
    )
    for r in el:
        rule.addRule(Rule.fromXML(r))
    return rule
