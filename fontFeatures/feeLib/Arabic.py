"""
Arabic Glyph Shaping
====================

The ``Arabic`` plugin automates the creation of Arabic positional shaping
features. However, it requires you to have a particular glyph naming
convention. To use it, you must first define three classes called ``inits``,
``medis`` and ``finas``::

    DefineClass @inits = /init$/;
    DefineClass @medis = /medi$/;
    DefineClass @finas = /fina$/;

Next, load the plugin and use the ``InitMediFina`` verb, which takes no
arguments::

    LoadPlugin Arabic;
    InitMediFina;

This will create the ``init``, ``medi`` and ``fina`` features by stripping
the suffix ``.init`` off all glyph names in the ``@inits`` class, ``.medi`` off
glyph names in the ``@medis`` class, and ``.fina`` off glyph names in the
``@finas`` class.

"""
class InitMediFina:
    takesBlock = False

    @classmethod
    def validate(self, tokens, verbaddress):
        from fontFeatures.parserTools import ParseError

        if len(tokens) > 0:
            raise ParseError("Too many arguments", verbaddress, self)
        return True

    @classmethod
    def store(self, parser, tokens):
        from fontFeatures.parserTools import ParseError

        for c in ["inits", "medis", "finas"]:
            if not c in parser.fea.namedClasses:
                raise ParseError("Expected class %s not defined" % c, (), self)
        return parser.parseString(
            """
      Feature init { Substitute @inits~init -> @inits; };
      Feature medi { Substitute @medis~medi -> @medis; };
      Feature fina { Substitute @finas~fina -> @finas; };
    """
        )
