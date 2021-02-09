"""
Including Other Files
=====================

FEE files may contain other files; to load another file, use the ``Include``
verb::

    Include anchors.fee;
"""

from . import HelperTransformer
import lark

import os

PARSEOPTS = dict(use_helpers=True)
GRAMMAR = """
?start: action
action: ESCAPED_STRING
"""
VERBS = ["Include", "IncludeFEA"]

def _file_to_string_or_error(parser, filename):
    # Try it relative to current file
    basedir = os.path.dirname(parser.current_file)
    trypath = os.path.join(basedir, filename)
    for p in [trypath, filename]:
        if os.path.exists(p):
            with open(p) as f:
                return f.read()
    raise ValueError("Could not include file %s" % filename)

class Include(HelperTransformer):
    def ESCAPED_STRING(self, tok):
        return tok.value[1:-1] # slice removes "'s

    def action(self, args):
        (filename,) = args
        return self.parser.parseString(_file_to_string_or_error(self.parser, filename))

from fontFeatures.feaLib import FeaUnparser

class IncludeFEA(Include):
    def action(self, args):
        (filename,) = args
        fea = FeaUnparser(_file_to_string_or_error(self.parser, filename))
        self.parser.fontfeatures += fea.ff
