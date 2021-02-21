import lark

import collections
import pathlib
import warnings

from importlib import import_module
from fontFeatures import FontFeatures
from fontFeatures.feeLib import GlyphSelector
from babelfont.font import Font
from more_itertools import collapse

GRAMMAR="""
    ?start: statement+

    %import python(COMMENT)
    %import common(LETTER, DIGIT, WS)
    %ignore WS // this only omits whitespace not handled by other rules. e.g. between statements
    %ignore COMMENT
"""

TESTVALUE_METRICS=["width", "lsb", "rsb", "xMin", "xMax", "yMin", "yMax", "rise", "fullwidth"]

HELPERS="""
    statement: verb args ";"
    verb: VERB
    args: arg* | (arg* "{{" statement* "}}" arg*)
    arg: ARG WS*

    VERB: /[A-Z]/ (LETTER | DIGIT | "_")+
    ARG: (/[^\s;]+/)

    STARTGLYPHNAME: LETTER | DIGIT | "_"
    MIDGLYPHNAME: STARTGLYPHNAME | "." | "-"
    BARENAME: STARTGLYPHNAME MIDGLYPHNAME*
    inlineclass: "[" (WS* (CLASSNAME | BARENAME))* "]"
    CLASSNAME: "@" BARENAME

    ANYTHING: /[^\s]/
    REGEX: "/" ANYTHING* "/"

    HEXDIGIT: /[0-9A-Fa-f]/
    UNICODEGLYPH: "U+" HEXDIGIT~1..6
    unicoderange: UNICODEGLYPH "=>" UNICODEGLYPH

    SUFFIXTYPE: ("." | "~")
    glyphsuffix: SUFFIXTYPE STARTGLYPHNAME+
    glyphselector: (unicoderange | UNICODEGLYPH | REGEX | BARENAME | CLASSNAME | inlineclass) glyphsuffix*

    valuerecord: SIGNED_NUMBER | fee_value_record | fea_value_record
    fee_value_record: "<" ( FEE_VALUE_VERB "=" integer_container )+ ">"
    FEE_VALUE_VERB: "xAdvance" | "xPlacement" | "yAdvance" | "yPlacement"
    fea_value_record: "<" integer_container integer_container integer_container integer_container ">"

    METRIC: {}
    metric_comparison: METRIC COMPARATOR integer_container 
    GLYPHVALUE: METRIC "[" BARENAME "]"

    NAMEDINTEGER: "$" BARENAME
    integer_container: NAMEDINTEGER | GLYPHVALUE | SIGNED_NUMBER
    COMPARATOR: ">=" | "<=" | "==" | "<" | ">"

    languages: "<<" (LANG "/" SCRIPT)+ ">>"
    SCRIPT: LETTER~3..4 // TODO: Validate
    LANG: LETTER~3..4 // TODO: Validate

    %import common(ESCAPED_STRING, SIGNED_NUMBER, NUMBER, LETTER, DIGIT, WS)
    %ignore WS
""".format(" | ".join(['"{}"'.format(tv) for tv in TESTVALUE_METRICS]))

# These are options usable by plugins to affect parsing. It is recommended to
# leave use_helpers True in almost all cases, unless you want to handle parsing
# of arguments at a low level in your plugin. The helpers parse things like
# glyph classes, regular expressions, etc. in a consistent way across different
# plugins.
PARSEOPTS = dict(use_helpers=True)

class NullParser:
    def parse(*args, **kwargs):
        pass

class Verb:
    transformer = None
    parser = None

class FeeParser:
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

    plugins = dict()
    variables = dict()
    current_file = pathlib.Path().absolute()

    parser = lark.Lark(HELPERS+GRAMMAR)

    def __init__(self, font):
        for p in self.DEFAULT_PLUGINS:
            self.load_plugin(p)

        self.font = font
        self.transformer = FeeTransformer(self)
        self.fontfeatures = FontFeatures()
        self.fontfeatures.setGlyphClassesFromFont(self.font)

    def load_plugin(self, plugin) -> bool:
        if "." not in plugin:
            resolved_plugin = "feeLib." + plugin

        mod = import_module(resolved_plugin)

        if not all([hasattr(mod, attr) for attr in ("PARSEOPTS", "GRAMMAR", "VERBS")]) or \
                not "use_helpers" in mod.PARSEOPTS:
            warnings.warn("Module {} is not a FEE plugin".format(resolved_plugin))
            return False

        return self.register_plugin(mod, plugin)

    def register_plugin(self, mod, plugin) -> bool:
        verbs = getattr(mod, "VERBS")
        popts = getattr(mod, "PARSEOPTS")
        rules = HELPERS+mod.GRAMMAR if popts["use_helpers"] else mod.GRAMMAR

        for v in verbs:
            verb = Verb()
            verb_grammar = getattr(mod, v+"_GRAMMAR", None)
            verb_bbgrammar = getattr(mod, v+"_beforebrace_GRAMMAR", None)
            verb_abgrammar = getattr(mod, v+"_afterbrace_GRAMMAR", None)
            
            if verb_grammar:
                verb.parser = lark.Lark(rules+verb_grammar)
            else:
                verb.parser = lark.Lark(rules)

            if verb_bbgrammar:
                verb.bbparser = lark.Lark(rules+verb_bbgrammar)
            else:
                verb.bbparser = NullParser()

            if verb_abgrammar:
                verb.abparser = lark.Lark(rules+verb_abgrammar)
            else:
                verb.abparser = NullParser()

            verb.transformer = getattr(mod, v)
            self.plugins[v] = verb

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
        return self.transformer.transform(self.parser.parse(s))

    def filterResults(self, results):
        ret = [x for x in collapse(results) if x and not isinstance(x, str)]
        return ret

class FeeTransformer(lark.Transformer):
    def __init__(self, parser):
        self.parser = parser

    def start(self, args):
        return args 

    def statement(self, args):
        verb, args = args
        #print("FeeTransformer.statement", verb, args)
        if verb not in self.parser.plugins:
            warnings.warn("Unknown verb: %s" % verb)
            return (verb, args)

        requested_plugin = self.parser.plugins[verb]

        # This branch is called for plugins that use `statement` in their grammar (and use_helpers), it allows the statements to resolve themselves so you aren't given the args as a string. Most such plugins use brackets, e.g. Feature, Routine
        tuple_idxs = list( (i for i,v in enumerate(args) if isinstance(v, tuple)) )
        if len(tuple_idxs) > 0:
            first_tuple_idx, last_tuple_idx = tuple_idxs[0], tuple_idxs[-1]
            statements = [args[ti] for ti in tuple_idxs]
            before = args[:first_tuple_idx]
            after = args[last_tuple_idx+1:]
            before_tree = requested_plugin.bbparser.parse(' '.join(before))
            after_tree  = requested_plugin.abparser.parse(' '.join(after))
            transformer = requested_plugin.transformer(self.parser)
            ret = []
            if before_tree:
                before_args = transformer.transform(before_tree)
                ret.insert(0, before_args if len(before_args) > 0 else None)
            else:
                ret.insert(0, None)
            ret.append(statements)
            if after_tree:
                after_args  = transformer.transform(after_tree)
                ret.append(after_args if len(after_args) > 0 else None)
            else:
                ret.append(None)
            verb_ret = (verb, transformer.action(ret))
        # For normal plugins that don't take statements
        elif len(args) == 0 or isinstance(args[0], str):
            tree = requested_plugin.parser.parse(' '.join(args))
            verb_ret = (verb, requested_plugin.transformer(self.parser).transform(tree))
        else:
            raise ValueError("Arguments of unknown type: {}".format(type(args)))

        #print("Parsed line...", verb_ret)
        return verb_ret

    def verb(self, args):
        assert len(args) == 1
        return args[0].value

    def args(self, args):
        return args

    def arg(self, args):
        return args[0].value

def _UNICODEGLYPH(u):
    return int(u[2:], 16)

class FEEVerb(lark.Transformer):
    def __init__(self, parser):
        self.parser = parser

    def beforebrace(self, args):
        return args

    def SIGNED_NUMBER(self, tok):
        return int(tok)

    def NAMEDINTEGER(self, tok):
        name = tok[1:] # all begin with $. but this doesn't match $1, $2 etc.
        if name in self.parser.variables:
            return self.parser.variables[name]
        else:
            return ValueError("Undefined variable: %s")

    def GLYPHVALUE(self, args):
        (metric, glyph) = args
        return self._get_metrics(glyph, metric)

    def glyphsuffix(self, args):
        (suffixtype, suffix) = args[0].value, "".join([a.value for a in args[1:]])
        return dict(suffixtype=suffixtype, suffix=suffix)

    def integer_container(self, args):
        (i,) = args
        return int(i)

    def unicoderange(self, args):
        return lark.Token("UNICODERANGE", range(_UNICODEGLYPH(args[0].value), _UNICODEGLYPH(args[1].value)+1), args[0].pos_in_stream)

    def inlineclass(self, args):
        return lark.Token("INLINECLASS", [{t.type.lower(): t.value} for t in args if t.type in ["BARENAME", "CLASSNAME"]])

    def glyphselector(self, args):
        token, suffixes = args[0], args[1:]
        if token.type == "CLASSNAME":
            token.value = token.value[1:]
        elif token.type == "REGEX":
            token.value = token.value[1:-1]
        elif token.type == "UNICODEGLYPH":
            token.value = _UNICODEGLYPH(token.value)
        return GlyphSelector({token.type.lower(): token.value}, suffixes, token.pos_in_stream)
