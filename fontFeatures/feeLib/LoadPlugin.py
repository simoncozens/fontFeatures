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

GRAMMAR = """
LoadPlugin_Args = <(letter|".")+>:x -> [x]
"""
VERBS = ["LoadPlugin"]
class LoadPlugin:
    @classmethod
    def action(self, parser, name):
        parser._load_plugin(name)
