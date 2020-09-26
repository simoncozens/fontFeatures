from lxml import etree

def toXML(self):
  root = etree.Element("routine")
  if self.flags: root.attrib["flags"] = self.flags
  if self.address: root.attrib["address"] = str(self.address)
  if self.name: root.attrib["name"] = self.name
  for r in self.rules:
    root.append(r.toXML())

  return root

@classmethod
def fromXML(klass, el):
  rule = klass(
      address = el.get("address"),
      name = el.get("name"),
      flags = el.get("flags")
  )
  for r in el:
      rule.addRule(Rule.fromXML(x))
  return rule
