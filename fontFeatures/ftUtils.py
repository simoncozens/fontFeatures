# Useful routines to get what we need from fontTools
import math
import statistics
from fontFeatures.ckmeans import ckmeans


def categorize_glyph(font, glyphname):
    gdef = font["GDEF"].table
    classdefs = gdef.GlyphClassDef.classDefs
    if not glyphname in classdefs:
        return ("unknown", None)
    if classdefs[glyphname] == 1:
        return ("base", None)
    if classdefs[glyphname] == 2:
        return ("ligature", None)
    if classdefs[glyphname] == 3:
        # Now find attachment class
        mclass = None
        if gdef.MarkAttachClassDef:
            markAttachClassDef = gdef.MarkAttachClassDef.classDefs
            if glyphname in markAttachClassDef:
                mclass = markAttachClassDef[glyphname]
        return ("mark", mclass)
    if classdefs[glyphname] == 4:
        return ("component", None)
    return ("unknown", None)


def set_glyph_category(font, glyphname, category, maClass=None):
    gdef = font["GDEF"].table
    classdefs = gdef.GlyphClassDef.classDefs
    if category == "base":
        classdefs[glyphname] = 1
    elif category == "ligature":
        classdefs[glyphname] = 2
    elif category == "mark":
        classdefs[glyphname] = 3
        if maClass and gdef.MarkAttachClassDef:
            gdef.MarkAttachClassDef.classDefs[glyphname] = maClass
    elif category == "component":
        classdefs[glyphname] = 4
    else:
        raise ValueError("Unknown category")


def get_glyph_metrics(font, glyphname):
    metrics = {
        "width": font["hmtx"][glyphname][0],
        "lsb": font["hmtx"][glyphname][1],
    }
    if "glyf" in font:
        glyf = font["glyf"][glyphname]
        try:
            metrics["xMin"], metrics["xMax"], metrics["yMin"], metrics["yMax"] = (
                glyf.xMin,
                glyf.xMax,
                glyf.yMin,
                glyf.yMax,
            )
        except Exception as e:
            metrics["xMin"], metrics["xMax"], metrics["yMin"], metrics["yMax"] = (
                0,
                0,
                0,
                0,
            )
    else:
        bounds = font.getGlyphSet()[glyphname]._glyph.calcBounds(font.getGlyphSet())
        metrics["xMin"], metrics["yMin"], metrics["xMax"], metrics["yMax"] = bounds
    metrics["rise"] = get_rise(font, glyphname)
    metrics["rsb"] = metrics["width"] - metrics["xMax"]
    return metrics


def get_rise(font, glyphname):
    # Find a cursive positioning feature or it's game over
    if "GPOS" not in font:
        return 0
    t = font["GPOS"].table
    cursives = filter(lambda x: x.LookupType == 3, font["GPOS"].table.LookupList.Lookup)
    anchors = {}
    for c in cursives:
        for s in c.SubTable:
            for glyph, record in zip(s.Coverage.glyphs, s.EntryExitRecord):
                anchors[glyph] = []
                if record.EntryAnchor:
                    anchors[glyph].append(
                        (record.EntryAnchor.XCoordinate, record.EntryAnchor.YCoordinate)
                    )
                if record.ExitAnchor:
                    anchors[glyph].append(
                        (record.ExitAnchor.XCoordinate, record.ExitAnchor.YCoordinate)
                    )
    if glyphname not in anchors:
        return 0
    if len(anchors[glyphname]) == 1:
        return anchors[glyphname][0][1]
    return anchors[glyphname][0][1] - anchors[glyphname][1][1]


def bin_glyphs_by_metric(font, glyphs, category, bincount=5):
    metrics = [(g, get_glyph_metrics(font, g)[category]) for g in glyphs]
    justmetrics = [x[1] for x in metrics]
    if bincount > len(glyphs):
        bincount = len(glyphs)
    clusters = ckmeans(justmetrics, bincount)
    binned = []
    for c in clusters:
        thiscluster = []
        for m in metrics:
            if m[1] in c:
                thiscluster.append(m)
        thiscluster = (
            [x[0] for x in thiscluster],
            int(statistics.mean([x[1] for x in thiscluster])),
        )
        binned.append(thiscluster)
    return binned


def determine_kern(
    font, glyph1, glyph2, targetdistance, offset1=(0, 0), offset2=(0, 0), maxtuck=0.4
):
    from beziers.path import BezierPath
    from beziers.point import Point

    paths1 = BezierPath.fromFonttoolsGlyph(font, glyph1)
    paths2 = BezierPath.fromFonttoolsGlyph(font, glyph2)
    offset1 = Point(*offset1)
    offset2 = Point(offset2[0] + font["hmtx"][glyph1][0], offset2[1])
    kern = 0
    lastBest = None

    iterations = 0
    while True:
        # Compute min distance
        minDistance = None
        closestpaths = None
        for p1 in paths1:
            p1 = p1.clone().translate(offset1)
            for p2 in paths2:
                p2 = p2.clone().translate(Point(offset2.x + kern, offset2.y))
                d = p1.distanceToPath(p2, samples=3)
                if not minDistance or d[0] < minDistance:
                    minDistance = d[0]
                    closestsegs = (d[3], d[4])
                    # import matplotlib.pyplot as plt

                    # fig, ax = plt.subplots()
                    # p1.clone().plot(ax, drawNodes=False)
                    # p2.clone().plot(ax)
                    # for s in closestsegs:
                    #     BezierPath.fromSegments([s]).plot(ax, drawNodes=False, color="red")
                    # plt.show()
        if not lastBest or minDistance < lastBest:
            lastBest = minDistance
        else:
            break  # Nothing helped
        if abs(minDistance - targetdistance) < 1 or iterations > 10:
            break
        iterations = iterations + 1
        kern = kern + (targetdistance - minDistance)

    if maxtuck:
        kern = max(kern, -(font["hmtx"][glyph1][0] * maxtuck))
    else:
        kern = max(kern, -(font["hmtx"][glyph1][0]))
    return int(kern)


def duplicate_glyph(font, existing, new):
    from babelfont.ttf.font import TTFont

    babelfont = TTFont(font)
    existingGlyph = babelfont.layers[0][existing]
    newGlyph = babelfont.layers[0].newGlyph(new)

    for c in existingGlyph.contours:
        newGlyph.appendContour(c)
    for c in existingGlyph.components:
        newGlyph.appendComponent(c)
    newGlyph.width = existingGlyph.width
