"""
Including Other Files
=====================

FEE files may contain other files; to load another file, use the ``Include``
verb::

    Include anchors.fee;
"""

import os

GRAMMAR = """
Include_Args = <(~';' anything)+>:filename -> (filename,)
IncludeFEA_Args = Include_Args
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

class Include:
    @classmethod
    def action(self, parser, filename):
        return parser.parseString(_file_to_string_or_error(parser, filename))

from fontFeatures.feaLib import FeaUnparser

class IncludeFEA:
    @classmethod
    def action(self, parser, filename):
        fea = FeaUnparser(_file_to_string_or_error(parser, filename))
        parser.fontfeatures += fea.ff
