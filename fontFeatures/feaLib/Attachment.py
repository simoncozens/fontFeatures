# Code for converting a Attachment object into feaLib statements
import fontTools.feaLib.ast as feaast
from glyphtools import categorize_glyph
import warnings
from fontFeatures.variableScalar import VariableScalar


def _glyphref(g):
    if len(g) == 1:
        return feaast.GlyphName(g[0])
    return feaast.GlyphClass([feaast.GlyphName(x) for x in g])


def sortByAnchor(self):
    anchors = {}
    for name, pos in self.marks.items():
        if not pos in anchors:
            anchors[pos] = []
        anchors[pos].append(name)
    self.markslist = [(v, k) for k, v in anchors.items()]

    anchors = {}
    for name, pos in self.bases.items():
        if not pos in anchors:
            anchors[pos] = []
        anchors[pos].append(name)
    self.baseslist = [(v, k) for k, v in anchors.items()]


def feaPreamble(self, ff):
    if self.is_cursive:
        return []
    sortByAnchor(self)
    if not "mark_classes_done" in ff.scratch:
        ff.scratch["mark_classes_done"] = {}
    b = feaast.Block()
    for mark in self.markslist:
        if not (self.base_name, tuple(mark[0])) in ff.scratch["mark_classes_done"]:
            b.statements.append(
                feaast.MarkClassDefinition(
                    feaast.MarkClass(self.base_name),
                    feaast.Anchor(int(mark[1][0]), int(mark[1][1])),
                    _glyphref(mark[0]),
                )
            )
            ff.scratch["mark_classes_done"][(self.base_name, tuple(mark[0]))] = True
    return [b]


def asFeaAST(self):
    b = feaast.Block()
    # if any(
    #     isinstance(x[0], VariableScalar) or isinstance(x[1], VariableScalar)
    #     for x in list(self.bases.values()) + list(self.marks.values())
    # ):
    #     raise ValueError("Can't directly express a variable anchor in FEA")
    if self.is_cursive:
        allglyphs = set(self.bases.keys()) | set(self.marks.keys())
        for g in allglyphs:
            b.statements.append(
                feaast.CursivePosStatement(
                    _glyphref([g]),
                    g in self.bases and feaast.Anchor(int(self.bases[g][0]),int(self.bases[g][1])),
                    g in self.marks and feaast.Anchor(int(self.marks[g][0]),int(self.marks[g][1])),
                )
            )
    else:
        if not hasattr(self, "baseslist"):
            sortByAnchor(self)  # e.g. when testing
        for base in self.baseslist:
            statementtype = feaast.MarkBasePosStatement
            if self.font:
                if categorize_glyph(self.font, base[0][0])[0] == "mark":
                    statementtype = feaast.MarkMarkPosStatement
            if self.force_markmark:
                statementtype = feaast.MarkMarkPosStatement
            b.statements.append(
                statementtype(
                    _glyphref(base[0]),
                    [[feaast.Anchor(int(base[1][0]), int(base[1][1])), feaast.MarkClass(self.base_name)]],
                )
            )

    return b
