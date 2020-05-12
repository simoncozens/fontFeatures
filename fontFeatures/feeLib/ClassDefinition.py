import re


class DefineClass:
    takesBlock = False

    @classmethod
    def validate(self, tokens, verbaddress):
        from fontFeatures.parserTools import ParseError

        if not tokens[0].token.startswith("@"):
            raise ParseError("Class name must start with '@'", tokens[0].address, self)

        if tokens[1].token != "=":
            raise ParseError(
                "Expected something to equal something else", tokens[1].address, self
            )

        if tokens[2].token.startswith("/"):
            if not tokens[-1].token.endswith("/"):
                raise ParseError(
                    "Unterminated regular expression", tokens[2].address, self
                )
        elif tokens[2].token.startswith("["):
            if not tokens[-1].token.endswith("]"):
                raise ParseError("Unterminated class", tokens[2].address, self)
        elif tokens[2].token.startswith("@"):
            if len(tokens) > 3:
                raise ParseError("Too many arguments given", verbaddress, self)
        else:
            raise ParseError("Can't understand class", self)

        return True

    @classmethod
    def store(self, parser, tokens):
        name = tokens[0].token[1:]
        if tokens[2].token.startswith("/"):
            glyphs = self.expandRegex(parser, tokens)
        if tokens[2].token.startswith("["):
            glyphs = self.expandClass(parser, tokens)
        if tokens[2].token.startswith("@"):
            glyphs = parser.expandGlyphOrClassName(tokens[2].token)
        parser.fea.namedClasses[name] = glyphs
        return []

    @classmethod
    def expandRegex(self, parser, tokens):
        regex = " ".join([x.token for x in tokens[2:]])
        regex = regex[1:-1]
        try:
            pattern = re.compile(regex)
        except Exception as e:
            raise ParseError(
                "Couldn't parse regular expression", tokens[2].address, self
            )
        return list(filter(lambda g: pattern.search(g), parser.glyphs))

    @classmethod
    def expandClass(self, parser, tokens):
        tokens[2].token = tokens[2].token[1:]
        tokens[-1].token = tokens[-1].token[:-1]
        glyphs = []
        for token in [t.token for t in tokens[2:]]:
            glyphs.extend(parser.expandGlyphOrClassName(token))
        return list(dict.fromkeys(glyphs))


class ShowClass:
    takesBlock = False

    @classmethod
    def validate(self, tokens, verbaddress):
        from fontFeatures.parserTools import ParseError

        if not tokens[0].token.startswith("@"):
            raise ParseError("Class name must start with '@'", tokens[0].address, self)
        if len(tokens) > 1:
            raise ParseError("Too many arguments given", verbaddress, self)

    @classmethod
    def store(self, parser, tokens):
        name = tokens[0].token
        print(
            "Expanding class %s -> [%s]"
            % (name, " ".join(parser.expandGlyphOrClassName(name)))
        )
        return []
