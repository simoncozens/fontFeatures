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
