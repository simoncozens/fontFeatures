from lxml import etree


def _toXML(self, root):
    self._makeglyphslots(root, "input", self.input)
    return root


@classmethod
def fromXML(klass, el):
  from fontFeatures import Routine
  rule = klass(
      klass._slotArray(klass, el.find("input")),
      precontext = klass._slotArray(klass, el.find("precontext")),
      postcontext = klass._slotArray(klass, el.find("postcontext")),
      address = el.get("address"),
      languages = el.get("languages"),
      flags = int(el.get("flags") or 0)
  )
  lookupsxml = el.find("lookups")
  rule.lookups = []
  for slot in lookupsxml:
    routines = [Routine.fromXML(x) for x in slot.findall("routine")]
    rule.lookups.append(routines)
  return rule
