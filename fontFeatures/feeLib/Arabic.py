"""
Arabic Glyph Shaping
====================

The ``Arabic`` plugin automates the creation of Arabic positional shaping
features. However, it requires you to have a particular glyph naming
convention: initial forms must end with ``.init``, medial forms with ``.medi``
and final forms with ``.fina``.

Next, load the plugin and use the ``InitMediFina`` verb, which takes no
arguments::

    LoadPlugin Arabic;
    InitMediFina;

This will define ``@init``, ``@media`` and ``@fina`` classes, and create
the ``init``, ``medi`` and ``fina`` features.

"""

GRAMMAR = """
InitMediFina_Args = ws;
"""

VERBS = ["InitMediFina"];

class InitMediFina:
    def action(self, parser):
        return parser.parseString(
            """
      DefineClass @inits = /init$/;
      DefineClass @medis = /medi$/;
      DefineClass @finas = /fina$/;
      Feature init { Substitute @inits~init -> @inits; };
      Feature medi { Substitute @medis~medi -> @medis; };
      Feature fina { Substitute @finas~fina -> @finas; };
    """
        )
