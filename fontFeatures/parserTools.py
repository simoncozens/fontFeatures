class ParseError(ValueError):
    pass


class Token:
    def __init__(self, token, address):
        self.token = token
        self.address = address


class ParseContext:
    def __init__(self, string):
        self.string = string
        self.line = 1
        self.char = 1
        self.cursor = 0

    @property
    def address(self):
        return (self.line, self.char)

    @property
    def moreToParse(self):
        return self.cursor < len(self.string)

    @property
    def currentChar(self):
        return self.string[self.cursor]

    def skipWhitespaceAndComments(self):
        while self.moreToParse and self.currentChar in " \t\n#":
            if self.currentChar == "#":
                self.consumeToEndOfLine()
            else:
                self.consume()

    def consume(self):
        c = self.currentChar
        self.char = self.char + 1
        if self.currentChar == "\n":
            self.line = self.line + 1
            self.char = 1
        self.cursor = self.cursor + 1
        return c

    def consumeToEndOfLine(self):
        while self.moreToParse and self.currentChar != "\n":
            self.consume()

    def expect(self, expectations):
        for e in expectations:
            if (
                len(self.string) >= self.cursor + len(e)
                and self.string[self.cursor : self.cursor + len(e)] == e
                and (
                    self.cursor + len(e) == len(self.string)
                    or self.string[self.cursor + len(e)] in " \n\t;}"
                )
            ):
                self.char = self.char + len(e)
                self.cursor = self.cursor + len(e)
                return e
        raise ParseError(
            "Expected one of %s, found %s"
            % (", ".join(expectations), self.consumeToken().token),
            self.address,
        )

    def consumeToken(self):
        token = ""
        startOfToken = self.address
        while self.moreToParse and not (self.currentChar in " \t;\n"):
            token = token + self.consume()
        self.skipWhitespaceAndComments()
        return Token(token, startOfToken)

    def consumeTokens(self):
        tokens = []
        while self.moreToParse and not (self.currentChar == ";"):
            token = self.consumeToken()
            tokens.append(token)
        self.expect([";"])
        return tokens

    def returnBlock(self):
        startOfBlock = self.address
        self.expect(["{"])
        self.skipWhitespaceAndComments()
        blockParts = []
        nesting = 0
        while self.moreToParse:
            if self.currentChar == "}":
                if nesting == 0:
                    break
                nesting = nesting - 1
            if self.currentChar == "{":
                nesting = nesting + 1
            token = self.consumeToken()
            blockParts.append(token.token)
            if self.currentChar == ";":
                blockParts.append(self.consume())
            self.skipWhitespaceAndComments()
        if not self.moreToParse and nesting > 0:
            raise ParseError("Block never ended", startOfBlock)
        self.expect(["}"])
        self.skipWhitespaceAndComments()
        self.expect([";"])
        return " ".join(blockParts)
