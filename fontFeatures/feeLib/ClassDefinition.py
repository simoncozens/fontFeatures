"""
Class Definitions
=================

To define a named glyph class in the FEE language, use the ``DefineClass``
verb. This takes three arguments: the first is a class name, which must
start with the ``@`` character; the second is the symbol ``=``; the third
is either a single classname (which may be suffixed - see below),  a regular
expression (``/.../``), or a set of glyphs and/or classes (which may be suffixed)
enclosed in square brackets (``[ ... ]``)::

    DefineClass @upper_alts = @upper.alt; # First format
    DefineClass @lower = /^[a-z]$/; # Second format
    DefineClass @upper_and_lower = [A B C D E F G @lower]; # Third format

Class Suffixes
--------------

In Fee, you may use "synthetic classes" anywhere that a class name is valid.
Synthetic classes are generating by taking existing named class name and adding
either ``.something`` or ``~something``. FEE will automatically create a class of
glyphs by adding or removing ``.something`` from glyphs within the given
class. For example, if you have::

    DefineClass @upper = [A B C D];

You can say::

    Substitute @upper -> @upper.alt;

to substitute the glyphs in ``[A B C D]`` for the glyphs
``[A.alt B.alt C.alt D.alt]``.

It is often easier, however, to deal with the problem the other way around.
Instead of having to remember which glyphs you have defined alternates for,
you can simply ask FEE to find glyphs ending ``.alt``::

    DefineClass @alternates = /\\.alt$/;

and then create a synthetic class which *removes* the dotted suffix by using
the ``~`` operator::

    Substitute @alternates~alt -> @alterates;

"""

import re
from fontFeatures.ftUtils import get_glyph_metrics
import warnings


GRAMMAR = """
predicate = ws 'and' ws '(' ws <letter+>:metric ws ('>='|'<='|'='|'<'|'>'):comparator ws <digit+>:value ws ')' -> {'predicate': metric, 'comparator': comparator, 'value': value}
andconjunction = glyphselector:l ws '&' ws primary:r -> {'conjunction': 'and', 'left': l, 'right': r}
orconjunction = glyphselector:l2 ws '|' ws primary:r2 -> {'conjunction': 'or', 'left': l2, 'right': r2}
primary_paren = '(' ws primary:p ws ')' -> p
primary =  primary_paren | orconjunction | andconjunction | glyphselector

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
        parser.fontfeatures.namedClasses[classname["classname"]] = glyphs

    @classmethod
    def resolve_definition(self, parser, primary):
        if isinstance(primary, dict) and "conjunction" in primary:
            left = set(self.resolve_definition(parser, primary["left"]))
            right = set(self.resolve_definition(parser, primary["right"]))
            if primary["conjunction"] == "or":
                return list(left | right)
            else:
                return list(left & right)
        else:
            return primary.resolve(parser.fontfeatures, parser.font)

    @classmethod
    def meets_predicate(self, glyphname, predicate, parser):
        metric = predicate["predicate"]
        comp = predicate["comparator"]
        if isinstance(predicate["value"], dict):
            v = predicate["value"]
            testvalue_metrics = get_glyph_metrics(parser.font, v["glyph"])
            if v["metric"] not in metrics:
                raise ValueError("Unknown metric '%s'" % metric)
            testvalue = testvalue_metrics[v["metric"]]
        else:
            testvalue = int(predicate["value"])

        metrics = get_glyph_metrics(parser.font, glyphname)
        if metric not in metrics:
            raise ValueError("Unknown metric '%s'" % metric)
        value = metrics[metric]
        if comp == ">":
            return value > testvalue
        elif comp == "<":
            return value < testvalue
        elif comp == ">=":
            return value >= testvalue
        elif comp == "<=":
            return value <= testvalue
        raise ValueError("Bad comparator (can't happen?)")


class DefineClassBinned(DefineClass):
    @classmethod
    def action(self, parser, metric, bincount, classname, definition):
        from fontFeatures.ftUtils import bin_glyphs_by_metric
        glyphs = self.resolve_definition(parser, definition[0])
        predicates = definition[1]
        for p in predicates:
            glyphs = list(filter(lambda x: self.meets_predicate(x, p, parser), glyphs))

        binned = bin_glyphs_by_metric(parser.font, glyphs, metric, bincount=int(bincount))
        for i in range(1, int(bincount) + 1):
            parser.fontfeatures.namedClasses["%s_%s%i" % (classname["classname"], metric, i)] = binned[i - 1][0]


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
