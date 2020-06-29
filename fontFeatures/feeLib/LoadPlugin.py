"""
Loading Plugins
===============

Additional functionality is provided by plugins, which register additional
FEE verbs. To load a plugin, use the ``LoadPlugin`` verb. This takes
the name of a Python module. If the name does *not* contain a period character,
the plugin is expected to be found under the ``fontFeatures.feeLib`` package::

    LoadPlugin IMatra; # Loads the plugin fontFeatures.feeLib.IMatra

To load a custom plugin of your own, specify a Python module with a period in
the name::

    LoadPlugin myTools.myFEEPlugin; # Loads myTools.myFEEPlugin

"""
class LoadPlugin:
    takesBlock = False
    arguments = 1

    @classmethod
    def validate(self, tokens, verbaddress):
        if len(tokens) > self.arguments:
            from fontFeatures.parserTools import ParseError

            raise ParseError("Too many arguments given", verbaddress, self)

        return True

    @classmethod
    def store(self, parser, tokens):
        parser.loadPlugin(tokens[0].token)
        return []
