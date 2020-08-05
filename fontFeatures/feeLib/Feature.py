"""
Features
========

To group a set of rules into a feature, use the ``Feature`` verb. This takes
a name and a block containing rules::

    Feature rlig {
        ...
    };

Note that in FEE syntax you must not repeat the feature name at the end of
the block, as is required in AFDKO syntax.
"""

GRAMMAR = """
Feature_Args = featurename:f ws '{' ws statement+:s '}' -> (f,s)

featurename = <letter (letter|digit){3}>
"""
VERBS = ["Feature"]


class Feature:
    @classmethod
    def action(self, parser, featurename, statements):
        if not featurename in parser.fontfeatures.features:
            parser.fontfeatures.features[featurename] = []
        import code

        code.interact(local=locals())
        parser.fontfeatures.addFeature(featurename, parser.filterResults(statements))
