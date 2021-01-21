import re
import parsley
import importlib, inspect
from fontFeatures import FontFeatures
from babelfont.font import Font
from ometa.grammar import OMeta
import warnings
from more_itertools import collapse


def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    return "# %s\n" % (message)


warnings.formatwarning = warning_on_one_line


def callRule(self):
    _locals = {"self": self}
    n1 = self._apply(self.rule_anything, "anything", [])
    n2 = self._apply(self.rule_anything, "anything", [])
    return self.foreignApply(n1[0], n1[0] + "_" + n2[0], self.globals, self.locals)


class GlyphSelector:
    def __init__(self, selector, suffixes, location):
        self.selector = selector
        self.suffixes = suffixes
        self.location = location

    def as_text(self):
        if "barename" in self.selector:
            returned = self.selector["barename"]
        elif "classname" in self.selector:
            returned = "@" + self.selector["classname"]
        elif "regex" in self.selector:
            returned = "/" + self.selector["regex"] + "/"
        elif "unicodeglyph" in self.selector:
            returned = "U+%04X" % self.selector["unicodeglyph"]
        elif "inlineclass" in self.selector:
            items = [
                GlyphSelector(i, (), self.location)
                for i in self.selector["inlineclass"]
            ]
            returned = "[" + " ".join([item.as_text() for item in items]) + "]"

        else:
            raise ValueError("Unknown selector type %s" % self.selector)
        for s in self.suffixes:
            returned = returned + s["suffixtype"] + s["suffix"]
        return returned

    def _apply_suffix(self, glyphname, suffix):
        if suffix["suffixtype"] == ".":
            glyphname = glyphname + "." + suffix["suffix"]
        else:
            if glyphname.endswith("." + suffix["suffix"]):
                glyphname = glyphname[: -(len(suffix["suffix"]) + 1)]
        return glyphname

    def resolve(self, fontfeatures, font, mustExist=True):
        returned = []
        assert isinstance(font, Font)
        glyphs = font.keys()
        if "barename" in self.selector:
            returned = [self.selector["barename"]]
        elif "unicodeglyph" in self.selector:
            cp = self.selector["unicodeglyph"]
            glyph = font.glyphForCodepoint(cp, fallback=False)
            if not glyph:
                raise ValueError(
                    "Font does not contain glyph for U+%04X (at %s)"
                    % (cp, self.location)
                )
            returned = [glyph]
        elif "inlineclass" in self.selector:
            returned = list(
                collapse(
                    [
                        GlyphSelector(i, (), self.location).resolve(fontfeatures, font)
                        for i in self.selector["inlineclass"]
                    ]
                )
            )
        elif "classname" in self.selector:
            classname = self.selector["classname"]
            if not classname in fontfeatures.namedClasses:
                raise ValueError(
                    "Tried to expand glyph class '@%s' but @%s was not defined (at %s)"
                    % (classname, classname, self.location)
                )
            returned = fontfeatures.namedClasses[classname]
        elif "regex" in self.selector:
            regex = self.selector["regex"]
            try:
                pattern = re.compile(regex)
            except Exception as e:
                raise ValueError(
                    "Couldn't parse regular expression '%s' at %s"
                    % (regex, self.location)
                )

            returned = list(filter(lambda x: re.search(pattern, x), glyphs))
        for s in self.suffixes:
            returned = [self._apply_suffix(g, s) for g in returned]
        if mustExist:
            notFound = list(filter(lambda x: x not in glyphs, returned))
            returned = list(filter(lambda x: x in glyphs, returned))
            if len(notFound) > 0:
                plural = ""
                if len(notFound) > 1:
                    plural = "s"
                glyphstring = ", ".join(notFound)
                warnings.warn(
                    "# Couldn't find glyph%s '%s' in font (at %s)"
                    % (plural, glyphstring, self.location)
                )
        return list(returned)


class FeeParser:
    """Convert a FEE file into a fontFeatures object.

    The resulting object is stored in the parser's ``fontFeatures`` property.

    Args:
        font: A TTFont object or glyphsLib GSFontMaster object.
    """

    basegrammar = """
feefile = wsc statement+
statement = verb:v wsc callRule(v "Args"):args ws ';' wsc -> parser.do(v, args)
rest_of_line = <('\\\n' | (~'\n' anything))*>
wsc = (comment | ' ' | '\t' | '\n')+ | ws
comment = '#' rest_of_line ws?
verb = <letter+>:x ?(x in self.valid_verbs) -> x

# Ways of specifying glyphs
classname = '@' <(letter|"_")+>:b  -> {"classname": b}
barename = <(letter|digit|"."|"_")+ (("."|"_"|"-") (letter|digit)+)*>:b -> {"barename": b}
hexdigit = anything:x ?(x in '0123456789abcdefABCDEF') -> x
unicodeglyphname = 'U+' <hexdigit+>:u -> {"unicodeglyph": int(u,16) }
inlineclass_member = (barename|classname):m ws? -> m
inlineclass_members = inlineclass_member+
inlineclass = '[' ws inlineclass_members:m ']' -> {"inlineclass": m}
regex = '/' <(~'/' anything)+>:r '/' -> {"regex": r}
glyphsuffix = ('.'|'~'):suffixtype <(letter|digit|"_")+>:suffix -> {"suffixtype":suffixtype, "suffix":suffix}
glyphselector = (unicodeglyphname | regex | barename | classname | inlineclass ):g glyphsuffix*:s -> GlyphSelector(g,s, self.input.position)

# Number things
bareinteger = ('-'|'+')?:sign <digit+>:i -> (-int(i) if sign == "-" else int(i))
namedinteger = '$' barename:b ?(b["barename"] in parser.variables) -> int(parser.variables[b["barename"]])
integer = namedinteger | bareinteger

# Value records

valuerecord = integer_value_record | fee_value_record | traditional_value_record
integer_value_record = integer:xAdvance -> (0, 0, xAdvance, 0)
traditional_value_record = '<' integer:xPlacement ws integer:yPlacement ws integer:xAdvance ws integer:yAdvance '>' -> (xPlacement, yPlacement, xAdvance, yAdvance)
fee_value_record = '<' ws fee_value_record_member+:m '>' -> { "members": m }
fee_value_record_member = ("xAdvance"| "xPlacement" | "yAdvance" | "yPlacement"):d '=' integer:pos ws -> {"dimension": d, "position": pos}

"""

    DEFAULT_PLUGINS = [
        "LoadPlugin",
        "ClassDefinition",
        "Conditional",
        "Feature",
        "Substitute",
        "Position",
        "Chain",
        "Anchors",
        "Routine",
        "Include",
        "Variables",
    ]

    def __init__(self, font):
        self.grammar = self._make_initial_grammar()
        self.grammar_generation = 1
        self.font = font
        self.fontfeatures = FontFeatures()
        self.current_file = None
        self.plugin_classes = {}
        self.current_feature = None
        self.font_modified = False
        self.variables = {}
        self._rebuild_parser()
        for plugin in self.DEFAULT_PLUGINS:
            self._load_plugin(plugin)

    def parseFile(self, filename):
        """Load a FEE features file.

        Args:
            filename: Name of the file to read.
        """
        with open(filename, "r") as f:
            data = f.read()
        self.current_file = filename
        return self.parseString(data)

    def parseString(self, s):
        """LoadFEE features information from a string.

        Args:
            s: Layout rules in FEE format.
        """
        fee = self.parser(s).feefile()
        if self.font_modified:
            warnings.warn("Font was modified")
        return fee

    def _rebuild_parser(self):
        self.parser = parsley.wrapGrammar(self.grammar)

    def _make_initial_grammar(self):
        g = parsley.makeGrammar(
            FeeParser.basegrammar,
            {"match": re.match, "GlyphSelector": GlyphSelector},
            unwrap=True,
        )
        g.globals["parser"] = self
        g.rule_callRule = callRule
        g.valid_verbs = ["LoadPlugin"]
        return g

    def _load_plugin(self, plugin):
        if "." not in plugin:
            plugin = "fontFeatures.feeLib." + plugin
        mod = importlib.import_module(plugin)
        if not hasattr(mod, "GRAMMAR"):
            warnings.warn("Module %s is not a FEE plugin" % plugin)
            return

        self._register_plugin(mod)

    def _register_plugin(self, mod):
        rules = mod.GRAMMAR
        verbs = getattr(mod, "VERBS", [])
        self.grammar_generation = self.grammar_generation + 1
        classes = inspect.getmembers(mod, inspect.isclass)
        self.grammar.valid_verbs.extend(verbs)
        newgrammar = OMeta.makeGrammar(
            rules, "Grammar%i" % self.grammar_generation
        ).createParserClass(self.grammar, {})
        newgrammar.globals = self.grammar.globals
        for v in verbs:
            self.grammar.globals[v] = newgrammar
        for c in classes:
            self.plugin_classes[c[0]] = c[1]
        self._rebuild_parser()

    def do(self, verb, args):
        return self.plugin_classes[verb].action(self, *args)

    def filterResults(self, results):
        return [x for x in collapse(results) if x]
