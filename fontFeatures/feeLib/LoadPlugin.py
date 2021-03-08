import lark

PARSEOPTS = dict(use_helpers=True)

# We need a Python package name here, but a bare glyph name looks
# just like one.
GRAMMAR = """
    ?start: action
    action: BARENAME

    %import common(WS, LETTER, DIGIT)
    %ignore WS
"""

VERBS = ["LoadPlugin"]

class LoadPlugin(lark.Transformer):
    def __init__(self, parser):
        self.parser = parser

    def action(self, args):
        self.parser.load_plugin(args[0].value)
        return args[0].value
