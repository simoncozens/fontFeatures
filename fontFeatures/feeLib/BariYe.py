"""
Bari Ye Processing
------------------

This plugin provides some verbs which are extremely useful for handling the
bari-ye sequence in the Nastaliq script, but which require a certain amount
of set-up in advance from the user.

First, you must define the following glyph classes:

- ``@inits``: all initial forms
- ``@medis``: all medial forms
- ``@bari_ye``: all forms of final bari ye or glyphs that you wish to treat
  *like* bari ye. For example, final jim and final choti ye may have "bari ye
  like tendencies" in that they have a large negative right sidebearing that
  requires nukta repositioning.
- ``@behs``: all glyphs which may "carry" nuktas and marks under the rasm;
  typically medial and initial beh forms, but also medial and initial jim.

With this set-up in place, the ``BariYe`` plugin provides you with two verbs:
``BYMoveDots`` moves nuktas or marks such as kasra to underneath the
swash of the bari ye (or jim
etc...) by computing the length of the swash, the width and rise of all
sequences, and emitting rules which match applicable sequences. ``BYMoveDots``
takes two arguments. The first depends on your preferred stylistic strategy
for handling bari ne nuktas: either ``AlwaysDrop``, which simply drops all
dots underneath the swash, or ``TryToFit`` which only drops those dots which
would not fit in the gap between the bari ye swash and the rasm. (One nice
trick is to put ``BYMoveDots TryToFit`` into an ``rlig`` feature,
and ``BYMoveDots AlwaysDrop`` into a stylistic set, so the user can choose
where the dots should be.) The second is the list of all nuktas or marks (e.g.
kasra) which sit under the rasm and need to be repositioned underneath the
bari ye swash. *Note carefully* that this class should *additionally* contain
a set of glyphs suffixed ``.yb`` which have no anchors defined. i.e. if your
two-dots-below glyph is called ``ddb``, then it should contain both ``ddb``
and ``ddb.yb``, a copy of ``ddb`` with no anchors. You can use the
``FontEngineering`` plugin to generate these glyphs on the fly if necessary.

The other verb, ``BYFixOverhang`` deals with the problem of short bari ye
sequences. Bari ye glyphs typically have a large negative right sidebearing,
which means that sequences like "ابے" need additional kerning to stop the
alif from being "drawn in" to the bari ye.

``BYFixOverhang`` takes an integer
value (an additional number of points to separate the end of the bari ye tail
and the following glyph), and computes rules which act only on short sequences;
it evalutes all possible short sequences (using width-binning to keep the number
of combinations to a reasonable number), computes the total width of each
sequence, compares this against the negative RSB of the bari ye, and
emits appropriate kerning rules to generate the desired separation. e.g.
``BYFixOverhang 10 @bariye`` will ensure that there are at least 10 points
between the end of the tail of each glyph in ``@bariye`` and any isolated/final
glyph preceding the sequence.

"""


import fontFeatures
from glyphtools import (
    categorize_glyph,
    get_glyph_metrics,
    bin_glyphs_by_metric,
    get_rise,
    get_run
)
from fontFeatures.pathUtils import get_bezier_paths
from beziers.line import Line
from beziers.point import Point
import warnings
import beziers
import itertools
import math
import statistics

GRAMMAR = """
BYMoveDots_Args = <('AlwaysDrop'|'TryToFit')>:w ws glyphselector:g -> [w,g]
BYFixOverhang_Args = <'-'? (digit+)>:overhang_padding ws glyphselector:g -> [overhang_padding, g]
"""

VERBS = ["BYMoveDots", "BYFixOverhang"]


def interleave(a, b):
    c = a + b
    c[::2] = a
    c[1::2] = b
    return c


def dropnone(a):
    return list(filter(None, a))


# Accuracy of width detector
accuracy1 = 5  # This creates O[(n • n+1)/2] lookups
# Accuracy of rise detector
accuracy2 = 5

failsafe_max_length = 4
failsafe_min_run = 100


class BYMoveDots:
    @classmethod
    def action(self, parser, w, below_dots):
        for c in ["inits", "medis", "bariye", "behs"]:
            if c not in parser.fontfeatures.namedClasses:
                raise ValueError("Please define @%s class before calling" % c)

        alwaysDrop = w == "AlwaysDrop"

        # OK, here's the plan of attack for bari ye.
        # First, we find the length of the longest possible sequence.
        # Smallest medi * n + smallest beh + smallest init -> length of bari yeh right tail
        medis = parser.fontfeatures.namedClasses["medis"]
        inits = parser.fontfeatures.namedClasses["inits"]
        behs = parser.fontfeatures.namedClasses["behs"]
        below_dots = below_dots.resolve(parser.fontfeatures, parser.font)
        smallest_medi_width = max(failsafe_min_run, min([get_run(parser.font, g) for g in medis]))
        smallest_init_beh_width = min(
            [get_run(parser.font, g) for g in (set(behs) & set(inits))]
        )
        smallest_init_beh = min(
            (set(behs) & set(inits)),
            key=lambda g: get_run(parser.font, g),
        )
        warnings.warn("Smallest medi width is %i" % smallest_medi_width)
        smallest_medi = min(medis, key=lambda g: get_run(parser.font, g))

        routines = []
        for bariye in parser.fontfeatures.namedClasses["bariye"]:
            warnings.warn("BariYe computation for %s" % bariye)
            entry_anchor = parser.fontfeatures.anchors[bariye]["entry"]
            bariye_tail = max(
                -get_glyph_metrics(parser.font, bariye)["rsb"],
                get_glyph_metrics(parser.font, bariye)["xMax"] - entry_anchor[0],
            )
            # bariye_tail += max(get_glyph_metrics(parser.font, dot)["width"] for dot in below_dots) / 2
            # # Increase tail by half the width of the widest nukta
            # bariye_tail += (
            #     max(
            #         [
            #             get_glyph_metrics(parser.font, g)["xMax"]
            #             - get_glyph_metrics(parser.font, g)["xMin"]
            #             for g in below_dots
            #         ]
            #     )
            #     / 2
            # )

            # Consider two cases.
            # First, the case where the beh is init and full of short medis
            maximum_sequence_length_1 = 1 + math.ceil(
                (bariye_tail - smallest_init_beh_width) / smallest_medi_width
            )
            warnings.warn(
                "Longest init beh sequence: %s"
                % " ".join(
                    [smallest_medi] * (maximum_sequence_length_1 - 1)
                    + [smallest_init_beh]
                )
            )
            # Second, the case where the init is not beh, but there are a bunch of medis,
            # one (or more) of which is a medi beh
            smallest_init_nonbeh_width = min(
                [max(get_rise(parser.font, g),failsafe_min_run) for g in (set(inits) - set(behs))]
            )
            smallest_medi_beh_width = min(
                [max(get_rise(parser.font, g),failsafe_min_run) for g in (set(medis) & set(behs))]
            )

            maximum_sequence_length_2 = 2 + math.ceil(
                (bariye_tail - smallest_init_nonbeh_width - smallest_medi_beh_width)
                / smallest_medi_width
            )

            maximum_sequence_length = min(failsafe_max_length, max(
                maximum_sequence_length_1, maximum_sequence_length_2
            ))
            warnings.warn("Max sequence width is %i" % maximum_sequence_length)

            # Next, let's create a chain rule for all nukta sequences
            dropBYsRoutine = fontFeatures.Routine(flags=0x0010)
            dropBYsRoutine.markFilteringSet = below_dots

            dropADotRoutine = fontFeatures.Routine()
            # Substitute those not ending .yb with those ending .yb
            below_dots_non_yb = list(
                sorted(filter(lambda x: not x.endswith(".yb"), below_dots))
            )
            below_dots_yb = list(
                sorted(filter(lambda x: x.endswith(".yb"), below_dots))
            )
            if len(below_dots_non_yb) != len(below_dots_yb):
                raise ValueError(
                    "Mismatch in @below_dots: %s has .yb suffix, %s does not"
                    % (below_dots_yb, below_dots_non_yb)
                )

            dropADotRoutine.addRule(
                fontFeatures.Substitution([below_dots_non_yb], [below_dots_yb])
            )

            maybeDropDotRoutine = fontFeatures.Routine(flags=0x0010)
            maybeDropDotRoutine.markFilteringSet = below_dots

            binned_medis = bin_glyphs_by_metric(
                parser.font, medis, "run", bincount=accuracy1
            )
            binned_inits = bin_glyphs_by_metric(
                parser.font, inits, "run", bincount=accuracy1
            )

            queue = [[[[bariye]]]]
            bin2mk = {"0": None, "1": below_dots}
            while len(queue) > 0:
                consideration = queue.pop(0)
                # import code; code.interact(local=locals())
                seq_length = sum([s[1] for s in consideration[:-1]])
                repsequence = [(s[0][0], s[1]) for s in consideration[:-1]]
                sequence = [s[0] for s in consideration]
                warnings.warn("Sequence %s total %i bariye_tail %i" % (repsequence, seq_length, bariye_tail))

                if seq_length > bariye_tail or len(consideration) > maximum_sequence_length:
                    continue

                lu = [None] * len(sequence)
                if alwaysDrop:
                    lu[0] = [dropADotRoutine]
                else:
                    lu[0] = [maybeDropDotRoutine]
                for j in range(0, 2 ** (len(sequence) - 1)):
                    binary = "{0:0%ib}" % (len(sequence) - 1)
                    marksequence = [bin2mk[x] for x in list(binary.format(j))]
                    # import code; code.interact(local=locals())
                    newsequence = dropnone(interleave(sequence, marksequence))
                    chainrule = fontFeatures.Chaining(
                        [below_dots], postcontext=newsequence, lookups=lu
                    )
                    # We don't combine the bins here precisely because they're
                    # disjoint sets and that means they can be expressed as a
                    # format 2 class-based rule! Wonderful!
                    dropBYsRoutine.addRule(chainrule)

                for m in binned_medis:
                    queue.append([list(m)] + consideration)

            if not alwaysDrop:
                # Check to see if it can fit in the gap, and only move it if it can't
                medis_by_rise = bin_glyphs_by_metric(
                    parser.font, medis, "rise", bincount=accuracy2
                )
                queue = [[[[bariye], get_glyph_metrics(parser.font, bariye)["rise"]]]]
                ybClearance = self.get_yb_clearance(parser, bariye)
                gapRequired = self.compute_threshold(parser, below_dots) - ybClearance
                warnings.warn(
                    "%i units of rise are required to fit a nukta in the gap"
                    % gapRequired
                )
                while len(queue) > 0:
                    consideration = queue.pop(0)
                    total_rise = sum([s[1] for s in consideration])
                    repsequence = [(s[0][0], s[1]) for s in consideration]
                    # warnings.warn("Sequence %s total rise %i required %i" % (repsequence, total_rise, gapRequired))
                    if (
                        total_rise > gapRequired
                        or len(consideration) > maximum_sequence_length
                    ):
                        # warnings.warn("Does not drop")
                        continue

                    sequence = [s[0] for s in consideration]
                    lu = [None] * len(sequence)
                    lu[0] = [dropADotRoutine]
                    chainrule = fontFeatures.Chaining(
                        [below_dots], postcontext=sequence, lookups=lu
                    )
                    maybeDropDotRoutine.addRule(chainrule)
                    # print("Drops %s"  % chainrule.asFea())
                    for m in medis_by_rise:
                        if total_rise + m[1] < gapRequired:
                            queue.append([list(m)] + consideration)

            # Add all the routines to the parser
            parser.fontfeatures.routines.append(dropADotRoutine)
            if not alwaysDrop:
                parser.fontfeatures.routines.append(maybeDropDotRoutine)
            routines.append(dropBYsRoutine)
        return routines

    @classmethod
    def get_yb_clearance(self, parser, bariye):
        font = parser.font
        paths = get_bezier_paths(font, bariye)
        path = paths[0]
        bounds = path.bounds()
        x_of_tail = get_rise(font.font, bariye)
        ray = Line(
            Point(x_of_tail - 0.1, bounds.bottom - 5),
            Point(x_of_tail + 0.1, bounds.top + 5),
        )
        intersections = []
        for seg in path.asSegments():
            intersections.extend(seg.intersections(ray))
        intersections = list(sorted(intersections, key=lambda i: i.point.y))
        i = intersections[-1]
        return i.point.y

    @classmethod
    def compute_threshold(self, parser, below_dots):
        from fontFeatures.ttLib import unparse

        font = parser.font
        behforms = list(
            filter(
                lambda g: g.startswith("BEm") or g.startswith("BEi"),
                parser.font.keys(),
            )
        )
        bottomOfDot = statistics.mean(
            [get_glyph_metrics(font, x)["yMin"] for x in below_dots]
        )

        if hasattr(parser.fontfeatures, "anchors"):
            anchor1_y = statistics.mean(
                [
                    parser.fontfeatures.anchors[x]["_bottom"][1]
                    for x in below_dots
                    if x in parser.fontfeatures.anchors
                ]
            )
            anchor2_y = statistics.mean(
                [
                    parser.fontfeatures.anchors[x]["bottom"][1]
                    for x in behforms
                    if x in parser.fontfeatures.anchors
                    and "bottom" in parser.fontfeatures.anchors[x]
                ]
            )
        else:
            # Find the anchors
            ff2 = unparse(font)
            if "mark" not in ff2.features:
                raise ValueError("No mark positioning for font!")
            rules = list(
                filter(
                    lambda r: below_dots[0] in r.marks
                    and any([m in r.bases for m in behforms]),
                    [x for y in ff2.features["mark"] for x in y.rules],
                )
            )
            if len(rules) < 1:
                raise ValueError("No nukta positioning?")
            r = rules[0]
            anchor1_y = r.marks[below_dots[0]][1]
            anchor2_y = statistics.mean(
                [r.bases[x][1] for x in behforms if x in r.bases]
            )
        displacement = anchor2_y - anchor1_y
        return -(bottomOfDot + displacement)

class BYFixOverhang:
    @classmethod
    def action(self, parser, overhang_padding, glyphs):
        for c in ["inits", "medis"]:
            if c not in parser.fontfeatures.namedClasses:
                raise ValueError("Please define @%s class before calling")

        medis = parser.fontfeatures.namedClasses["medis"]
        inits = parser.fontfeatures.namedClasses["inits"]
        overhangers = glyphs.resolve(parser.fontfeatures, parser.font)

        binned_medis = bin_glyphs_by_metric(parser.font, medis, "run", bincount=8)
        binned_inits = bin_glyphs_by_metric(parser.font, inits, "run", bincount=8)
        rules = []
        maxchainlength = 0
        longeststring = []
        for yb in overhangers:
            entry_anchor = parser.fontfeatures.anchors[yb]["entry"]
            overhang = max(
                -get_glyph_metrics(parser.font, yb)["rsb"],
                get_glyph_metrics(parser.font, yb)["xMax"] - entry_anchor[0],
            )

            workqueue = [[x] for x in binned_inits]
            while workqueue:
                string = workqueue.pop(0)
                totalwidth = sum([ max(x[1],failsafe_min_run) for x in string])
                if totalwidth > overhang or len(string) > failsafe_max_length:
                    continue

                adjustment = overhang - totalwidth + int(overhang_padding)
                postcontext = [x[0] for x in string[:-1]] + [[yb]]
                input_ = string[-1]
                example = [input_[0][0]] + [x[0] for x in postcontext]
                warnings.warn("For glyphs in %s, overhang=%i totalwidth=%i adjustment=%i" % (example, overhang,totalwidth, adjustment))
                maxchainlength = max(maxchainlength, len(string))

                rules.append(
                    fontFeatures.Positioning(
                        [input_[0]],
                        [fontFeatures.ValueRecord(xAdvance=int(adjustment))],
                        postcontext=postcontext,
                    )
                )
                for medi in binned_medis:
                    workqueue.append([medi] + string)
        warnings.warn(
            "Bari Ye collision maximum chain length was %i glyphs" % maxchainlength
        )
        return [fontFeatures.Routine(rules=rules, flags=8)]
