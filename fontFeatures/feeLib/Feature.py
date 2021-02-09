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

For some features, like the Stylistic Sets (``ss01``-``ss20``), you can specify
a ``FeatureName``. If supported by the software it's displayed to the user::

    Feature ss01 {
        FeatureName "Half-width hiragana";
        ....
    };
"""

GRAMMAR = """
FEATURENAME: LETTER (LETTER | DIGIT)~3
"""

Feature_GRAMMAR = """
?start: action
action: FEATURENAME "{" statement+ "}"
"""

Feature_beforebrace_GRAMMAR = """
?start: beforebrace
beforebrace: FEATURENAME
"""
#FeatureName_Args = '"' <~'"' anything >+:name '"' -> (name,)

#featurename = <letter (letter|digit){3}>
#"""
PARSEOPTS = dict(use_helpers=True)
VERBS = ["Feature"]#, "FeatureName"]

from . import HelperTransformer
from fontFeatures import Routine, Rule

class Feature(HelperTransformer):
    def FEATURENAME(self, tok):
        return tok.value

    def beforebrace(self, args):
        return args

    def action(self, args):
        (featurename, statements, _) = args
        featurename = featurename[0]

        results = self.parser.filterResults(statements)
        self.parser.current_feature = featurename
        oddStatements = []
        def wrap_and_flush():
            nonlocal oddStatements
            
            if len(oddStatements) > 0:
                self.parser.fontfeatures.addFeature(featurename, [Routine(rules=[r for r in oddStatements if isinstance(r, Rule)])])
            oddStatements = []

        for r in results:
            if isinstance(r, Routine):
                wrap_and_flush()
                self.parser.fontfeatures.addFeature(featurename, [r])
            else:
                oddStatements.append(r)

        wrap_and_flush()
        self.parser.current_feature = None

        return statements

"""
class FeatureName:
    @classmethod
    def action(self, parser, name):
      pass
"""
