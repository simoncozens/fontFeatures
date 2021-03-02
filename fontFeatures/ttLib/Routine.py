import fontTools.otlLib.builder as otl


def toOTLookup(self, font):
    lookuptypes = [x.lookup_type() for x in self.rules]
    if not all([lu == lookuptypes[0] for lu in lookuptypes]):
        raise ValueError("For now, a routine can only contain rules of the same type")

    if self.stage == "pos":
        return buildPos(self, font, lookuptypes[0])
    if self.stage == "sub":
        return buildSub(self, font, lookuptypes[0])


def buildPos(self, font, lookuptype):
    if lookuptype == 1:
        builder = otl.SinglePosBuilder(font, self.address)
        for rule in self.rules:
            ot_valuerecs = [
                x.toOTLookup(pairPosContext=False) for x in rule.valuerecords
            ]
            builder.addPos(rule.address, rule.glyphs[0], ot_valuerecs[0])

    elif lookuptype == 2:
        builder = otl.PairPosBuilder(font, self.address)
        for rule in self.rules:
            ot_valuerecs = [
                x.toOTLookup(pairPosContext=True) for x in rule.valuerecords
            ]
            if len(rule.glyphs[0]) == 1 and len(rule.glyphs[1]) == 1:
                builder.addGlyphPair(
                    rule.address,
                    rule.glyphs[0][0],
                    ot_valuerecs[0],
                    rule.glyphs[1][0],
                    ot_valuerecs[1],
                )
            else:
                builder.addClassPair(
                    rule.address,
                    rule.glyphs[0],
                    ot_valuerecs[0],
                    rule.glyphs[1],
                    ot_valuerecs[1],
                )
    elif lookuptype == 3:
        builder = otl.CursivePosBuilder(font, self.address)
        for rule in self.rules:
            allglyphs = set(rule.bases.keys()) | set(rule.marks.keys())
            for g in allglyphs:
                builder.attachments[g] = (
                    g in rule.bases and otl.buildAnchor(*rule.bases[g]) or None,
                    g in rule.marks and otl.buildAnchor(*rule.marks[g]) or None,
                )
    else:
        raise ValueError("Don't know how to build a POS type %i lookup" % lookuptype)
    builder.lookupflag = self.flags
    # XXX mark filtering set
    return builder.build()


def buildSub(self, font, lookuptype):
    if lookuptype == 1:
        builder = otl.SingleSubstBuilder(font, self.address)
        for rule in self.rules:
            builder.mapping[rule.input[0][0]] = rule.replacement[0][0]
    elif lookuptype == 2:
        builder = otl.MultipleSubstBuilder(font, self.address)
        for rule in self.rules:
            builder.mapping[rule.input[0][0]] = [ x[0] for x in rule.replacement ]
    else:
        raise ValueError("Don't know how to build a SUB type %i lookup" % lookuptype)

    builder.lookupflag = self.flags
    # XXX mark filtering set
    return builder.build()
