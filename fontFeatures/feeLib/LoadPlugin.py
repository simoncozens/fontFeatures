import lark

PARSEOPTS = dict(use_helpers=True)

GRAMMAR = """
    ?start: action
    action: VERB

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
