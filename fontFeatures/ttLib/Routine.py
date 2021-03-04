import fontTools.otlLib.builder as otl
from fontTools.varLib.builder import buildVarDevTable
from fontFeatures.variableScalar import VariableScalar


def toOTLookup(self, font, ff):
    lookuptypes = [x.lookup_type() for x in self.rules]
    if not all([lu == lookuptypes[0] for lu in lookuptypes]):
        raise ValueError("For now, a routine can only contain rules of the same type")

    if self.stage == "pos":
        return buildPos(self, font, lookuptypes[0], ff)
    if self.stage == "sub":
        return buildSub(self, font, lookuptypes[0], ff)


def makeAnchor(anchor, ff):
    x,y = anchor
    if isinstance(x, VariableScalar):
        x_def, x_index = x.add_to_variation_store(ff.varstorebuilder)
    else:
        x_def, x_index = x, None
    if isinstance(y, VariableScalar):
        y_def, y_index = y.add_to_variation_store(ff.varstorebuilder)
    else:
        y_def, y_index = y, None
    anchor = otl.buildAnchor(x_def, y_def)
    if x_index is not None and x_index != 0xFFFF:
        anchor.XDeviceTable = buildVarDevTable(x_index)
        anchor.Format = 3
    if y_index is not None and x_index != 0xFFFF:
        anchor.YDeviceTable = buildVarDevTable(y_index)
        anchor.Format = 3
    return anchor


def buildPos(self, font, lookuptype, ff):
    if lookuptype == 1:
        builder = otl.SinglePosBuilder(font, self.address)
        for rule in self.rules:
            ot_valuerecs = [
                x.toOTValueRecord(ff, pairPosContext=False) for x in rule.valuerecords
            ]
            for glyph in rule.glyphs[0]:
                builder.add_pos(rule.address, glyph, ot_valuerecs[0])
    elif lookuptype == 2:
        builder = otl.PairPosBuilder(font, self.address)
        for rule in self.rules:
            ot_valuerecs = [
                x.toOTValueRecord(ff, pairPosContext=True) for x in rule.valuerecords
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
                    g in rule.bases and makeAnchor(rule.bases[g], ff) or None,
                    g in rule.marks and makeAnchor(rule.marks[g], ff) or None,
                )
    elif lookuptype == 4 or lookuptype == 6:
        if lookuptype == 4:
            builder = otl.MarkBasePosBuilder(font, self.address)
            baseholder = builder.bases
        else:
            builder = otl.MarkMarkPosBuilder(font, self.address)
            baseholder = builder.baseMarks
        marktypes = list(set([x.mark_name for x in self.rules]))
        for r in self.rules:
            markclass = marktypes.index(r.mark_name)
            for mark, anchor in r.marks.items():
                builder.marks[mark] = (markclass, makeAnchor(anchor, ff))
            for base, anchor in r.bases.items():
                if base not in baseholder:
                    baseholder[base] = {}
                baseholder[base][markclass] = makeAnchor(anchor, ff)
    else:
        raise ValueError("Don't know how to build a POS type %i lookup" % lookuptype)
    builder.lookupflag = self.flags
    # XXX mark filtering set
    return builder.build()


def buildSub(self, font, lookuptype, ff):
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
