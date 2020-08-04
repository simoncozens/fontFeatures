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


class DefineClass:
    takesBlock = False

    @classmethod
    def validate(self, tokens, verbaddress):
        from fontFeatures.parserTools import ParseError

        if not tokens[0].token.startswith("@"):
            raise ParseError("Class name must start with '@'", tokens[0].address, self)

        if tokens[1].token != "=":
            raise ParseError(
                "Expected something to equal something else", tokens[1].address, self
            )

        if tokens[2].token.startswith("/"):
            if not tokens[-1].token.endswith("/"):
                raise ParseError(
                    "Unterminated regular expression", tokens[2].address, self
                )
        elif tokens[2].token.startswith("["):
            if not tokens[-1].token.endswith("]"):
                raise ParseError("Unterminated class", tokens[2].address, self)
        elif tokens[2].token.startswith("@"):
            if len(tokens) > 3:
                raise ParseError("Too many arguments given", verbaddress, self)
        else:
            raise ParseError("Can't understand class", self)

        return True

    @classmethod
    def store(self, parser, tokens):
        name = tokens[0].token[1:]
        if tokens[2].token.startswith("/"):
            glyphs = self.expandRegex(parser, tokens)
        elif tokens[2].token.startswith("["):
            glyphs = self.expandClass(parser, tokens)
        elif tokens[2].token.startswith("@"):
            glyphs = parser.expandGlyphOrClassName(tokens[2].token)
        parser.fea.namedClasses[name] = glyphs
        return []

    @classmethod
    def expandRegex(self, parser, tokens):
        regex = " ".join([x.token for x in tokens[2:]])
        regex = regex[1:-1]
        try:
            pattern = re.compile(regex)
        except Exception as e:
            raise ParseError(
                "Couldn't parse regular expression", tokens[2].address, self
            )
        return list(filter(lambda g: pattern.search(g), parser.glyphs))

    @classmethod
    def expandClass(self, parser, tokens):
        tokens[2].token = tokens[2].token[1:]
        tokens[-1].token = tokens[-1].token[:-1]
        glyphs = []
        for token in [t.token for t in tokens[2:]]:
            glyphs.extend(parser.expandGlyphOrClassName(token))
        return list(dict.fromkeys(glyphs))


class ShowClass:
    takesBlock = False

    @classmethod
    def validate(self, tokens, verbaddress):
        from fontFeatures.parserTools import ParseError

        if not tokens[0].token.startswith("@"):
            raise ParseError("Class name must start with '@'", tokens[0].address, self)
        if len(tokens) > 1:
            raise ParseError("Too many arguments given", verbaddress, self)

    @classmethod
    def store(self, parser, tokens):
        name = tokens[0].token
        print(
            "Expanding class %s -> [%s]"
            % (name, " ".join(parser.expandGlyphOrClassName(name)))
        )
        return []
