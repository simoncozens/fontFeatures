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
Feature_Args = featurename:f wsc '{' wsc statement+:s '}' -> (f,s)
FeatureName_Args = '"' <~'"' anything >+:name '"' -> (name,)

featurename = <letter (letter|digit){3}>
"""
VERBS = ["Feature", "FeatureName"]

from fontFeatures import Routine

class Feature:
    @classmethod
    def action(self, parser, featurename, statements):
        results = parser.filterResults(statements)
        parser.current_feature = featurename
        oddStatements = []
        def wrap_and_flush():
          nonlocal oddStatements
          if len(oddStatements) > 0:
            parser.fontfeatures.addFeature(featurename, [Routine(rules=oddStatements)])
          oddStatements = []

        for r in results:
          if isinstance(r, Routine):
            wrap_and_flush()
            parser.fontfeatures.addFeature(featurename, [r])
          else:
            oddStatements.append(r)
        wrap_and_flush()
        parser.current_feature = None


class FeatureName:
    @classmethod
    def action(self, parser, name):
      pass
