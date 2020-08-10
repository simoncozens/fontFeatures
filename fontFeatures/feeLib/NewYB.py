import fontFeatures
from fontFeatures.jankyPOS import JankyPos
from fontFeatures.ftUtils import categorize_glyph, get_glyph_metrics, bin_glyphs_by_metric, get_rise
from fontFeatures.pathUtils import get_bezier_paths
from beziers.line import Line
from beziers.point import Point
import warnings
import beziers
import itertools
import math
import statistics

GRAMMAR = """
NewYB_Args = <('AlwaysDrop'|'TryToFit')>:w -> [w]
"""

VERBS = ["NewYB"]


# Accuracy of width detector
accuracy1 = 5 # This creates O[(n • n+1)/2] lookups
# Accuracy of rise detector
accuracy2 = 10

class NewYB:
    @classmethod
    def action(self, parser, w):
        for c in ["inits", "medis", "bariye", "below_dots"]:
            if c not in parser.fontfeatures.namedClasses:
                raise ValueError("Please define @%s class before calling")

        alwaysDrop = w == "AlwaysDrop"

        # OK, here's the plan of attack for bari ye.
        # First, we find the length of the longest possible sequence.
        # Smallest medi * n + smallest init -> length of bari yeh right tail
        medis = parser.fontfeatures.namedClasses["medis"]
        inits = parser.fontfeatures.namedClasses["inits"]
        # Only support one bariye for now
        bariye = parser.fontfeatures.namedClasses["bariye"][0]
        below_dots = parser.fontfeatures.namedClasses["below_dots"]
        smallest_medi_width = min([ get_glyph_metrics(parser.font,g)["width"] for g in medis ])
        smallest_init_width = min([ get_glyph_metrics(parser.font,g)["width"] for g in inits ])
        smallest_init = min(inits, key = lambda g: get_glyph_metrics(parser.font,g)["width"])
        bariye_tail = -get_glyph_metrics(parser.font,bariye)["rsb"]
        maximum_sequence_length = math.ceil((bariye_tail - smallest_init_width) / smallest_medi_width)

        # Next, let's create a chain rule for all single-nukta sequences
        dropSingleDotRoutine = fontFeatures.Routine(flags= 0x0010)
        dropSingleDotRoutine.markFilteringSet = below_dots

        r = fontFeatures.Routine(flags= 0x0010)
        r.markFilteringSet = below_dots
        for i in range (0,maximum_sequence_length):
            for j in range(0,i+1):
                sequence = [inits] + [medis] * j + [below_dots] + [medis] * (i-j) + [[bariye]]
                lu = [None]*len(sequence)
                lu[j+1] = [dropSingleDotRoutine]
                r.addRule(fontFeatures.Chaining(sequence, lookups=lu))

        # Now we have an [init, medi*(n = 0..max), nukta] sequence
        # For now, we're just going to drop them all.
        dropADotRoutine = fontFeatures.Routine()
        dropADotRoutine.addRule(fontFeatures.Substitution([below_dots], [["sdb.yb","ddb.yb","tdb.yb"]]))

        maybeDropDotRoutine = fontFeatures.Routine(flags= 0x0010)
        maybeDropDotRoutine.markFilteringSet = below_dots


        binned_medis = bin_glyphs_by_metric(parser.font, medis, "width", bincount=accuracy1)
        binned_inits = bin_glyphs_by_metric(parser.font, inits, "width", bincount=accuracy1)

        warnings.warn("Evaluating single-dot bari ye sequences")
        queue = [[[[bariye]]]]
        while len(queue) > 0:
            consideration = queue.pop(0)
            # import code; code.interact(local=locals())
            seq_length = sum([ s[1] for s in consideration[:-1] ])
            repsequence = [ (s[0][0], s[1]) for s in consideration[:-1] ]
            sequence = [ s[0] for s in consideration]
            # warnings.warn("Sequence %s total %i bariye_tail %i" % (repsequence, seq_length, bariye_tail))

            if seq_length > bariye_tail: continue
            lu = [None]*len(sequence)
            if alwaysDrop:
                lu[0] = [dropADotRoutine]
            else:
                lu[0] = [maybeDropDotRoutine]
            chainrule = fontFeatures.Chaining([below_dots],postcontext=sequence, lookups=lu)
            # We don't combine the bins here precisely because they're
            # disjoint sets and that means they can be expressed as a
            # format 2 class-based rule! Wonderful!
            dropSingleDotRoutine.addRule(chainrule)
            for m in binned_medis:
                queue.append([list(m)] + consideration)

        if not alwaysDrop:
            # Check to see if it can fit in the gap, and only move it if it can't
            medis_by_rise = bin_glyphs_by_metric(parser.font, medis, "rise", bincount=accuracy2)
            queue = [[[[bariye],get_rise(parser.font,bariye)]]]
            ybClearance = self.get_yb_clearance(parser.font, bariye)
            gapRequired = self.compute_threshold(parser, below_dots) - ybClearance
            warnings.warn("%i units of rise are required to fit a nukta in the gap" % gapRequired)
            while len(queue) > 0:
                consideration = queue.pop(0)
                total_rise = sum([ s[1] for s in consideration ])
                repsequence = [ (s[0][0], s[1]) for s in consideration ]
                # warnings.warn("Sequence %s total rise %i required %i" % (repsequence, total_rise, gapRequired))
                if total_rise > gapRequired or len(consideration) > maximum_sequence_length:
                    # warnings.warn("Does not drop")
                    continue

                sequence = [ s[0] for s in consideration]
                lu = [None]*len(sequence)
                lu[0] = [dropADotRoutine]
                chainrule = fontFeatures.Chaining([below_dots],postcontext=sequence, lookups=lu)
                maybeDropDotRoutine.addRule(chainrule)
                # print("Drops %s"  % chainrule.asFea())
                for m in medis_by_rise:
                    if total_rise + m[1] < gapRequired:
                        queue.append([list(m)] + consideration )


        # Add all the routines to the parser
        parser.fontfeatures.addRoutine(dropADotRoutine)
        if not alwaysDrop:
            parser.fontfeatures.addRoutine(maybeDropDotRoutine)
        parser.fontfeatures.addRoutine(dropSingleDotRoutine)
        return [r]

    @classmethod
    def get_yb_clearance(self, font, bariye):
        paths = get_bezier_paths(font, bariye)
        path = paths[0]
        bounds = path.bounds()
        x_of_tail = get_glyph_metrics(font, bariye)["width"]
        ray = Line(Point(x_of_tail - 0.1, bounds.bottom - 5), Point(x_of_tail + 0.1, bounds.top + 5))
        intersections = []
        for seg in path.asSegments():
            intersections.extend(seg.intersections(ray))
        intersections = list(sorted(intersections, key=lambda i: i.point.y))
        i1, i2 = intersections[0:2]
        return i2.point.y

    @classmethod
    def compute_threshold(self, parser, below_dots):
        from fontFeatures.ttLib import unparse
        font = parser.font
        # Find the anchors
        ff2 = unparse(font)
        behforms = list(filter(lambda g: g.startswith("BEm") or g.startswith("BEi"), parser.font.getGlyphOrder()))
        if "mark" not in ff2.features:
            raise ValueError("No mark positioning for font!")
        rules = list(filter(lambda r: below_dots[0] in r.marks and any([m in r.bases for m in behforms]), [x for y in ff2.features["mark"] for x in y.rules]))
        if len(rules) < 1:
            raise ValueError("No nukta positioning?")
        r = rules[0]
        anchor1_y = r.marks[below_dots[0]][1]
        anchor2_y = statistics.mean([r.bases[x][1] for x in behforms if x in r.bases])
        displacement = anchor2_y - anchor1_y
        bottomOfDot = statistics.mean([get_glyph_metrics(font, x)["yMin"] for x in below_dots])
        return -(bottomOfDot + displacement)
