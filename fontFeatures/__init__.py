"""
The FontFeatures class is a way of representing the transformations -
substitutions and positionings - going on inside a font at a semantically
high level. It aims to be independent of and unconstrained by the OpenType
representation, with the assumption that these high-level objects can be
either "compiled down" into AFDKO feature code or directly written to the
GSUB/GPOS tables of a font.

FontFeatures aims to marshal data between OTF binary representations,
AFDKO feature code, FontDame, and a new language called FEE (Font
Engineering language with Extensibility).

A FontFeatures representation of a font will make use of two other top-level
concepts: Features and Routines. Routines are collections of rules; they play
a similar function to the AFDKO concept of a lookup, but unlike lookups,
Routines do not need to be comprised of rules of the same type. You can think
of them as functions that are called on a glyph string.
"""

from fontTools.ttLib import TTFont
from collections import OrderedDict
from fontTools.feaLib.ast import ValueRecord
from itertools import chain
from bidict import bidict


class FontFeatures:
    """An object representing the layout rules in a font."""
    def __init__(self):
        self.namedClasses = bidict({})
        self.routines = []
        self.features = OrderedDict()
        self.anchors = {}
        self.symbols = {}
        self.scratch = {}  # Space for items to communicate context to each other. :(
        self.doneUsageMarking = False

    def gensym(self, category):
        if not category in self.symbols:
            self.symbols[category] = 0
        self.symbols[category] += 1
        return f'{category}{self.symbols[category]}'

    def addRoutine(self, r):
        """Add a Routine to the preamble.

        Args:
            r: A :py:class:`Routine` object.
        """
        assert isinstance(r, Routine)
        self.routines.append(r)
        r.parent = self

    def getNamedClassFor(self, glyphs, name):
        """Find and optionally stores a named class of glyphs

        Args:
            glyphs: A sequence of glyph names.
            name: A name for this glyph class if it does not exist.

        Returns:
            The name of a glyph class. If the exact same set of glyphs
            was already stored as a glyph class, then the name of that
            class will be returned. If not, then the class will be stored
            and the name provided as the ``name`` argument will be returned.
        """
        if tuple(glyphs) in self.namedClasses.inverse:
            return self.namedClasses.inverse[tuple(glyphs)]
        self.namedClasses[name] = tuple(glyphs)
        return name

    def addFeature(self, name, rs):
        """Add Routines to a named feature.

        Args:
            name: The feature name.
            rs: A sequence of :py:class:`Routine` objects.
        """
        if not name in self.features:
            self.features[name] = []
        for r in rs:
            r.parent = self
            self.features[name].append(r)

    def allRoutines(self):
        """Return all Routines in the font.

        Returns:
            Routines stored in the preamble and within features.
        """
        routines = set(self.routines)
        for k, v in self.features.items():
            for n in v:
                if isinstance(n, Routine):
                    routines.add(n)
        return list(routines)

    def allRules(self, ruletype=None):
        """Return all rules in the font, optionally filtered by type

        Args:
            ruletype: A class (``Positioning``, ``Substitution`` etc)
                to filter the results.

        Returns:
            Routines stored in the preamble and within features.
        """

        rules = []
        for r in self.allRoutines():
            rules.extend(r.rules)
        for k, v in self.features.items():
            for n in v:
                if isinstance(n, Routine):
                    rules.extend(n.rules)

        if ruletype:
            rules = filter(lambda x: isinstance(x, ruletype), rules)
        return rules

    def markRoutineUseInChains(self):
        """Annotate routines which are used in chaining rules.

        Generally used when converting the fontFeatures object to another
        format; allows routines to know where they are being used by annotating
        them with the ``.usedin`` property for optimization purposes.
        """
        if self.doneUsageMarking:
            return
        for r in self.allRoutines():
            r.usedin = set()
        for chain in self.allRules(Chaining):
            for routinelist in chain.lookups:
                if not routinelist:
                    continue
                for routine in routinelist:
                    # Using a set here so it is safe to call more than once
                    routine.usedin.add(chain)
        self.doneUsageMarking = True

    from .feaLib.FontFeatures import asFea, asFeaAST

    def hoist_languages(self):
        """Sort routines into scripts and languages and resolve wildcards."""
        scripts = OrderedDict()
        count = 0

        def add_language(p):
            nonlocal scripts
            nonlocal count
            s, l = p
            if not s in scripts:
                scripts[s] = []
            if l == "*":
                return
            if not l in scripts[s]:
                count = count + 1
                scripts[s].append(l)

        for k in self.routines:
            if k.languages:
                for l in k.languages:
                    add_language(l)
        for feat in self.features.values():
            for thing in feat:
                if hasattr(thing, "languages") and thing.languages:
                    for l in thing.languages:
                        add_language(l)

        if count > 0 and not "DFLT" in scripts:
            scripts["DFLT"] = []
            scripts.move_to_end("DFLT", last=False)
        if count > 0 and not "dflt" in scripts["DFLT"]:
            scripts["DFLT"].insert(0, "dflt")

        self.scripts_and_languages = scripts


class Routine:
    """Represent a Routine (similar to OT Lookup).

    A routine is a set of rules, sometimes but always with an explicit name.
    It can apply to a set of language/script pairs.
    """
    def __init__(
        self,
        name="",
        rules=None,
        address=None,
        inlined=False,
        languages=None,
        parent=None,
        flags=0,
    ):
        self.name = name
        self.usedin = set()
        if rules:
            self.rules = rules
        else:
            self.rules = []
        self.address = address
        self.comments = []
        self.inlined = inlined
        self.languages = languages
        self.parent = parent
        self.flags = flags

    def addRule(self, rule):
        """Adds a rule to a Routine.

        Args:
            rule: A ``Substitution``, ``Positioning``, etc. object.
        """
        assert isinstance(rule, Rule)
        self.rules.append(rule)

    def addComment(self, comment):
        """Adds a comment to a Routine.

        Comments are emitted when the Routine is converted to text formats
        such as AFDKO.

        Args:
            comment: A string comment.
        """
        self.comments.append(comment)

    @property
    def involved_glyphs(self):
        """Returns the names of all of the glyphs involved in this Routine."""
        return set.union(*[r.involved_glyphs for r in self.rules])

    from .feaLib.Routine import asFea, asFeaAST, feaPreamble


class Rule:
    def asFea(self):
        """Returns this Rule as a string of AFDKO feature text."""
        return self.asFeaAST().asFea()

    def feaPreamble(self, ff):
        """Computes any text that needs to go in the feature file header."""
        return []


class Substitution(Rule):
    """Represents a Substitution rule.

    A substitution represents any kind of exchange of one set of glyphs for
    another: single substitutions, multiple substitutions and ligatures are all
    substitutions. Optionally, substitutions may be followed by precontext and
    postcontext.

    Args:
        input_: A list of lists. The outer list represents the positions in
            the glyph stream to substitute, with the inner list representing
            the glyph names at each position.
        replacement: A list of glyph names.
        precontext: A list of list of glyphs which must appear before the input
            sequence.
        postcontext: A list of list of glyphs which must appear before the input
            sequence.
        lookups: A list of list of lookups to be applied to the glyph sequence.
            The outer list represents the positions in the input sequence, with
            the inner list containing Routines to apply.
        reverse: Boolean representing if the substitutions should take place from
            the end of the string.
  """

    def __init__(
        self,
        input_,
        replacement,
        precontext=None,
        postcontext=None,
        address=None,
        languages=None,
        lookups=None,
        reverse=False,
        flags=0,
    ):
        self.precontext = precontext or []
        self.postcontext = postcontext or []
        self.input = input_
        self.replacement = replacement
        self.address = address
        self.lookups = lookups or []
        self.languages = languages
        self.flags = flags
        self.reverse = reverse

    @property
    def involved_glyphs(self):
        i = set(chain.from_iterable(self.input))
        o = set(chain.from_iterable(self.replacement))
        b = set(chain.from_iterable(self.precontext))
        a = set(chain.from_iterable(self.postcontext))
        return i | o | b | a

    from .feaLib.Substitution import asFeaAST


class Chaining(Rule):
    """Represents a Chain rule.

    A Chain rule represents the operation of calling another Routine when
    a particular input context is met.

    Args:
        input_: A list of lists. The outer list represents the positions in
            the glyph stream to substitute, with the inner list representing
            the glyph names at each position.
        precontext: A list of list of glyphs which must appear before the input
            sequence.
        postcontext: A list of list of glyphs which must appear before the input
            sequence.
        lookups: A list of list of lookups to be applied to the glyph sequence.
            The outer list represents the positions in the input sequence, with
            the inner list containing Routines to apply.
    """
    def __init__(
        self,
        input_,
        precontext=None,
        postcontext=None,
        address=None,
        languages=None,
        lookups=None,
        flags=0,
    ):
        self.precontext = precontext or []
        self.postcontext = postcontext or []
        self.input = input_
        self.address = address
        self.lookups = lookups or []
        self.languages = languages
        self.flags = flags

    from .feaLib.Chaining import asFeaAST, feaPreamble

    @property
    def involved_glyphs(self):
        i = set(chain.from_iterable(self.input))
        b = set(chain.from_iterable(self.precontext))
        a = set(chain.from_iterable(self.postcontext))
        return i | b | a


class Positioning(Rule):
    """Represents a Positioning rule.

    Args:
        input_: A list of lists. The outer list represents the positions in
            the glyph stream to position, with the inner list representing
            the glyph names at each glyph stream position.
        valuerecords: A list of ``ValueRecord`` objects to be applied at each
            glyph stream position.
        precontext: A list of list of glyphs which must appear before the input
            sequence.
        postcontext: A list of list of glyphs which must appear before the input
            sequence.
  """
    def __init__(
        self,
        glyphs,
        valuerecords,
        precontext=None,
        postcontext=None,
        address=None,
        languages=None,
        flags=0,
    ):
        self.precontext = precontext or []
        self.postcontext = postcontext or []
        assert len(glyphs) == len(valuerecords)
        self.glyphs = glyphs
        self.valuerecords = valuerecords
        self.address = address
        self.languages = languages
        self.flags = flags

    @property
    def involved_glyphs(self):
        i = set(chain.from_iterable(self.glyphs))
        b = set(chain.from_iterable(self.precontext))
        a = set(chain.from_iterable(self.postcontext))
        return i | b | a

    from .feaLib.Positioning import asFeaAST


class Attachment(Rule):
    """Represents an Attachment rule.

    Args:
        base_name: Name of the base class.
        mark_name: Name of the mark class.
        bases: Dictionary. They keys are names of glyphs to act as bases to
            the attachment (this may be categorized as mark glyphs if the
            attachment is a mark-to-mark operation); the associated values are
            a two-element tuple with the coordinates of the anchor.
        marks: Dictionary. They keys are names of glyphs to act as marks;
            the associated values are a two-element tuple with the coordinates
            of the anchor.
  """
    def __init__(
        self, base_name, mark_name, bases=None, marks=None, flags=0, address=None,
        font=None
    ):
        self.base_name = base_name
        self.mark_name = mark_name
        self.bases = bases or {}
        self.marks = marks or {}
        self.flags = flags
        self.address = address
        self.font = font

    @property
    def is_cursive(self):
        return self.base_name == "cursive_entry" or self.base_name == "entry" # XXX

    from .feaLib.Attachment import asFeaAST, feaPreamble

    @property
    def involved_glyphs(self):
        b = set(self.bases.keys())
        m = set(self.marks.keys())
        return b | m
