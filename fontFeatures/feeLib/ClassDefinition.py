"""
Class Definitions
=================

To define a named glyph class in the FEE language, use the ``DefineClass``
verb. This takes three arguments: the first is a class name, which must
start with the ``@`` character; the second is the symbol ``=``; the third
is a glyph selector as described above::

    DefineClass @upper_alts = @upper.alt;
    DefineClass @lower = /^[a-z]$/;
    DefineClass @upper_and_lower = [A B C D E F G @lower];

In addition, glyph classes can be *combined* within the ``DefineClass``
statement using intersection (``|``) and union (``&``) operators::

    DefineClass @all_marks = @lower_marks | @upper_marks;
    DefineClass @uppercase_vowels = @uppercase & @vowels;

As well as subtracted (``-``):

    DefineClass @ABCD = A | B | C | D;
    DefineClass @ABC = @ABCD - D;

Finally, glyph classes can be filtered through the use of one or more
*predicates*, which take the form ``and`` followed by a
bracketed relationship, and which tests the properties of the glyphs
against the expression given::

    DefineClass @short_behs = /^BE/ and (width < 200);

- The first part of the relationship is a metric, which can be one of

  - ``width`` (advance width)
  - ``lsb`` (left side bearing)
  - ``rsb`` (right side bearing)
  - ``xMin`` (minimum X coordinate)
  - ``xMax`` (maximum X coordinate)
  - ``yMin`` (minimum Y coordinate)
  - ``yMax`` (maximum Y coordinate)
  - ``rise`` (difference in Y coordinate between cursive entry and exit)
  - ``fullwidth`` (``xMax``-``xMin``)

- The second part is a comparison operator (``>=``, ``<=``,
  ``=``, ``<``, or ``>``).

- The third is either an integer or a metric name and the name of a
  single glyph in brackets.

This last form is best understood by example. The following definition
selects all members of the glyph class ``@alpha`` whose advance width is
less than the advance width of the ``space`` glyph::

    DefineClass @shorter_than_space = @alpha and (width < width(space));

- As well as testing for glyph metrics, the following other relationships
  are defined:

  - ``hasglyph(regex string)`` (true if glyph after replacement of regex by
    string exists in the font)
  - ``hasanchor(anchorname)`` (true if the glyph has the named anchor)
  - ``category(base)`` (true if the glyph has the given category)

Binned Definitions
------------------

Sometimes it is useful to split up a large glyph class into a number of
smaller classes according to some metric, in order to treat them
differently. For example, when performing an i-matra substitution in
Devanagari, you would generally want to split your base glyphs by width,
and apply the appropriate matra for each set of glyphs. FEE calls the
operation of organising glyphs into groups of similar metrics "binning".

The ``ClassDefinition`` plugin also provides the ``DefineClassBinned`` verb,
which generated a set of related glyph classes. The arguments of ``DefineClassBinned``
are identical to that of ``DefineClass``, except that after the class name
you must specify an open square bracket, the metric to be used to bin the
glyphs, a comma, the number of bins to create, and a close bracket, like so::

    DefineClassBinned @bases[width,5] = @bases;

This will create five classes, called ``@bases_width1`` .. ``@bases_width5``,
grouped in increasing order of advance width. Note that the size of the bins is
not guaranteed to be equal, but glyphs are clustered according to the similarity
of their metric. For example, if the advance widths are 99, 100, 110, 120,
500, and 510 and two bins are created, four glyphs will be in one bin and two
will be in the second.

(This is just an example for the purpose of explaining binning. We'll show a
better way to handle the i-matra question later.)

Glyph Class Debugging
---------------------

The combination of the above rules allows for extreme flexibility in creating
glyph classes, to the extent that it may become difficult to understand the
final composition of glyph classes! To alleviate this, the verb ``ShowClass``
will take any glyph selector and display its contents on standard error.

"""

import re
from glyphtools import get_glyph_metrics, bin_glyphs_by_metric

import warnings


GRAMMAR = """
predicate = ws 'and' ws ( has_glyph_predicate | category_predicate | has_anchor_predicate | comp_predicate )
comp_predicate = 'not'?:n ws  '(' ws <letter+>:metric ws ('>='|'<='|'='|'<'|'>'):comparator ws (<digit+>|bracketed_metric):value ws ')' -> {'predicate': metric, 'comparator': comparator, 'value': value, 'inverted': n}
has_anchor_predicate = 'not'?:n ws 'hasanchor(' barename:anchor ')' -> {'predicate': 'hasanchor', 'value': anchor["barename"], 'inverted':n }
has_glyph_predicate = 'not'?:n ws 'hasglyph(' regex:replace ws barename:withs ')' -> {'predicate': 'hasglyph', 'value': {'replace': replace["regex"], 'with': withs["barename"]}, 'inverted':n }
category_predicate = 'not'?:n ws 'category(' barename:cat ')' -> {'predicate': 'category', 'value': cat["barename"], 'inverted':n }
bracketed_metric = <letter+>:metric '(' <(letter|digit|"."|"_")+>:glyph ')' -> {'metric': metric, 'glyph': glyph}
conjunction = glyphselector:l ws ('&'|'|'|'-'):conjunction ws primary:r -> {'conjunction': {"&":"and","|":"or","-":"subtract"}[conjunction], 'left': l, 'right': r}

primary_paren = '(' ws primary:p ws ')' -> p
primary = primary_paren | conjunction | glyphselector

DefineClass_Args = classname:c ws '=' ws definition:d -> (c,d)
definition = primary:g predicate*:p -> (g,p)

DefineClassBinned_Args = classname:c '[' <letter+>:metric ws "," ws <digit+>:bincount ']' ws '=' ws definition:d -> (metric, bincount, c,d)

ShowClass_Args = glyphselector:g -> (g,)
"""

VERBS = ["DefineClass", "ShowClass", "DefineClassBinned"]

class DefineClass:
    @classmethod
    def action(self, parser, classname, definition):
        glyphs = self.resolve_definition(parser, definition[0])
        predicates = definition[1]
        for p in predicates:
            glyphs = list(filter(lambda x: self.meets_predicate(x, p, parser), glyphs))
        parser.fontfeatures.namedClasses[classname["classname"]] = tuple(glyphs)

    @classmethod
    def resolve_definition(self, parser, primary):
        if isinstance(primary, dict) and "conjunction" in primary:
            left = set(self.resolve_definition(parser, primary["left"]))
            right = set(self.resolve_definition(parser, primary["right"]))
            if primary["conjunction"] == "or":
                return list(left | right)
            elif primary["conjunction"] == "and":
                return list(left & right)
            else: #subtract
                return set(left) - set(right)
        else:
            return primary.resolve(parser.fontfeatures, parser.font)

    @classmethod
    def meets_predicate(self, glyphname, predicate, parser):
        inverted = predicate["inverted"]
        metric = predicate["predicate"]
        if metric == "hasanchor":
            anchor = predicate["value"]
            truth = glyphname in parser.fontfeatures.anchors and anchor in parser.fontfeatures.anchors[glyphname]
        elif metric == "category":
            cat = predicate["value"]
            truth = parser.font[glyphname].category == cat
        elif metric == "hasglyph":
            truth = re.sub(predicate["value"]["replace"], predicate["value"]["with"], glyphname) in parser.font
        else:
            comp = predicate["comparator"]
            if isinstance(predicate["value"], dict):
                v = predicate["value"]
                testvalue_metrics = get_glyph_metrics(parser.font, v["glyph"])
                if v["metric"] not in testvalue_metrics:
                    raise ValueError("Unknown metric '%s'" % metric)
                testvalue = testvalue_metrics[v["metric"]]
            else:
                testvalue = int(predicate["value"])

            metrics = get_glyph_metrics(parser.font, glyphname)
            if metric not in metrics:
                raise ValueError("Unknown metric '%s'" % metric)
            value = metrics[metric]
            if comp == ">":
                truth = value > testvalue
            elif comp == "<":
                truth = value < testvalue
            elif comp == ">=":
                truth = value >= testvalue
            elif comp == "<=":
                truth = value <= testvalue
            else:
                raise ValueError("Bad comparator %s (can't happen?)" % comp)
        if inverted:
            truth = not truth
        return truth

class DefineClassBinned(DefineClass):
    @classmethod
    def action(self, parser, metric, bincount, classname, definition):
        glyphs = self.resolve_definition(parser, definition[0])
        predicates = definition[1]
        for p in predicates:
            glyphs = list(filter(lambda x: self.meets_predicate(x, p, parser), glyphs))

        binned = bin_glyphs_by_metric(parser.font, glyphs, metric, bincount=int(bincount))
        for i in range(1, int(bincount) + 1):
            parser.fontfeatures.namedClasses["%s_%s%i" % (classname["classname"], metric, i)] = tuple(binned[i - 1][0])


class ShowClass:
    @classmethod
    def action(self, parser, classname):
        warnings.warn(
            "%s = %s"
            % (
                classname.as_text(),
                " ".join(classname.resolve(parser.fontfeatures, parser.font)),
            )
        )
        return []
