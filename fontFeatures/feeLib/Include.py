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
"""
VERBS = ["Include"]

class Include:
    @classmethod
    def action(self, parser, filename):
        # Try it relative to current file
        basedir = os.path.dirname(parser.current_file)
        trypath = os.path.join(basedir, filename)
        if os.path.exists(trypath):
          return parser.parseFile(trypath)
        if os.path.exists(filename):
          return parser.parseFile(filename)
        raise ValueError("Could not include file %s" % filename)

