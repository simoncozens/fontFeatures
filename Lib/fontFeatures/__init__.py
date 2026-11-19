"""
The FontFeatures class is a way of representing the transformations -
substitutions and positionings - going on inside a font at a semantically
high level. It aims to be independent of and unconstrained by the OpenType
representation, with the assumption that these high-level objects can be
either "compiled down" into AFDKO feature code or directly written to the
GSUB/GPOS tables of a font.

FontFeatures aims to marshal data between OTF binary representations,
AFDKO feature code, FontDame, and can power other representations such as the
FEZ language (see the 'fez' library).

A FontFeatures representation of a font will make use of two other top-level
concepts: Features and Routines. Routines are collections of rules; they play
a similar function to the AFDKO concept of a lookup, but unlike lookups,
Routines do not need to be comprised of rules of the same type. You can think
of them as functions that are called on a glyph string.

Here is an example of constructing a simple feature file using fontFeatures::

    ff = FontFeatures()

    liga_ffi = Substitution( [ ["f"], ["f"], ["i"] ], replacement=[["f_f_i"]] )
    liga_ffl = Substitution( [ ["f"], ["f"], ["l"] ], replacement=[["f_f_l"]] )
    liga_fi = Substitution( [ ["f"], ["i"] ], replacement=[["fi"]] )
    liga_ff = Substitution( [ ["f"], ["f"] ], replacement=[["f_f"]] )
    liga_routine = Routine(rules=[liga_ffi, liga_ffl, liga_fi, liga_ff])

    ff.addFeature("liga", [liga_routine])

    # Export Adobe syntax
    print(ff.asFea())

    font = TTFont("Test.ttf")
    ff.buildBinaryFeatures(font)
    font.save("Test-liga.ttf")
"""

from __future__ import annotations

from copy import copy
from itertools import chain
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from fontTools.feaLib.ast import ValueRecord as feaLibValueRecord
from fontTools.feaLib.variableScalar import VariableScalar

#: A list of glyph names which match a single position in the glyph stream.
GlyphClass = Sequence[str]
#: A list of glyph classes, one for each position in a rule's input sequence.
GlyphClasses = Sequence[GlyphClass]
#: A ``(script, language)`` pair, e.g. ``("latn", "dflt")``.
ScriptLanguage = Tuple[str, str]
#: The position of an anchor in font design units. Values may also be
#: :py:class:`fontTools.feaLib.variableScalar.VariableScalar` objects.
AnchorPosition = Tuple[
    Union[int, float, VariableScalar], Union[int, float, VariableScalar]
]
#: A routine, or a reference to one, as used in chain rule lookups.
Lookup = Union["Routine", "RoutineReference"]

RuleT = TypeVar("RuleT", bound="Rule")


class FontFeatures:
    """An object representing the layout rules in a font.

    The initializer has no parameters."""

    def __init__(self) -> None:
        #: A mapping of named classes to the glyph names which make up the class.
        self.namedClasses: Dict[str, GlyphClass] = {}
        #: All of the layout routines used in this font.
        self.routines: List[Routine] = []
        #: An ordered mapping of feature tags to lists of routine references.
        self.features: Dict[str, List[RoutineReference]] = {}
        #: A mapping of glyph names to a mapping of anchor names to positions.
        self.anchors: Dict[str, Dict[str, AnchorPosition]] = {}
        #: A mapping of symbol categories to the last generated symbol number.
        self.symbols: Dict[str, int] = {}
        #: A mapping of glyph names to their categories.
        self.glyphclasses: Dict[str, str] = {}
        #: Space for items to communicate context to each other.
        self.scratch: Dict[str, Any] = {}
        #: Scripts and languages supported by these features, keyed by script
        #: tag. Filled in by :py:meth:`hoist_languages`.
        self.scripts_and_languages: Dict[str, List[str]] = {}
        self.doneUsageMarking: bool = False

    def __add__(self, other: FontFeatures) -> FontFeatures:
        """Combine two FontFeatures objects together."""
        combined = FontFeatures()
        combined.namedClasses = {**self.namedClasses, **other.namedClasses}
        combined.routines = self.routines + other.routines
        combined.features = {**self.features, **other.features}
        combined.anchors = {**self.anchors, **other.anchors}
        combined.symbols = {**self.symbols, **other.symbols}
        combined.glyphclasses = {**self.glyphclasses, **other.glyphclasses}
        return combined

    def gensym(self, category: str) -> str:
        """Generate a new unique symbol (used for labeling unlabeled data).

        Args:
            category: The category for this symbol.

        Returns:
            A string representing a unique label.
        """
        if category not in self.symbols:
            self.symbols[category] = 0
        self.symbols[category] += 1
        return f"{category}{self.symbols[category]}"

    def routineNamed(self, name: str) -> Routine:
        """Finds a routine with the given name.

        Args:
            name: The name to find.

        Returns:
            The :py:class:`Routine` object with that name.

        Raises:
            ValueError: If no routine with that name is present.
        """
        for r in self.routines:
            if r.name == name:
                return r
        raise ValueError("Can't find routine '%s'" % name)

    def referenceRoutine(
        self, r: Routine, do_usecount: bool = True
    ) -> RoutineReference:
        """Store a routine and return a reference to it.

        Args:
            r: A :py:class:`Routine` object.
            do_usecount: Whether to increment the routine's usage count.
        """
        assert isinstance(r, Routine)

        if r not in self.routines:
            self.routines.append(r)
        r.parent = self
        if do_usecount:
            r.usecount = r.usecount + 1
        return RoutineReference(routine=r)

    def getNamedClassFor(self, glyphs: Sequence[str], name: str) -> str:
        """Find and optionally store a named class of glyphs.

        Args:
            glyphs: A sequence of glyph names.
            name: A name for this glyph class if it does not exist.

        Returns:
            The name of a glyph class. If the exact same set of glyphs was
            already stored as a glyph class, then the name of that class will
            be returned. If not, then the class will be stored and the name
            provided as the ``name`` argument will be returned.
        """
        for k, v in self.namedClasses.items():
            if sorted(glyphs) == sorted(v):
                return k
        self.namedClasses[name] = glyphs
        return name

    def addFeature(
        self, name: str, rs: Iterable[Union[Routine, RoutineReference]]
    ) -> None:
        """Add Routines to a named feature.

        Args:
            name: The feature name.
            rs: A sequence of :py:class:`Routine` or
                :py:class:`RoutineReference` objects.
        """
        if name not in self.features:
            self.features[name] = []
        for r in rs:
            r.parent = self
            if isinstance(r, Routine):
                r = self.referenceRoutine(r)
            self.features[name].append(r)

    @overload
    def allRules(self) -> List[Rule]: ...

    @overload
    def allRules(self, ruletype: Type[RuleT]) -> List[RuleT]: ...

    def allRules(self, ruletype: Optional[Type[Rule]] = None) -> List[Rule]:
        """Return all rules in the font, optionally filtered by type.

        Args:
            ruletype: A class (``Positioning``, ``Substitution`` etc) to filter
                the results by.

        Returns:
            All rules in the routines stored in this font features object.
        """
        rules: List[Rule] = list(
            chain.from_iterable(routine.rules for routine in self.routines)
        )
        if ruletype is not None:
            rules = [rule for rule in rules if isinstance(rule, ruletype)]
        return rules

    def markRoutineUseInChains(self) -> None:
        """Annotate routines which are used in chaining rules.

        Generally used when converting the fontFeatures object to another
        format; allows routines to know where they are being used by annotating
        them with the ``.usedin`` property for optimization purposes.
        """
        if self.doneUsageMarking:
            return
        for r in self.routines:
            r.usedin = set()
        for chain_rule in self.allRules(Chaining):
            for routinelist in chain_rule.lookups:
                if not routinelist:
                    continue
                for lookup in routinelist:
                    # Using a set here so it is safe to call more than once
                    if isinstance(lookup, RoutineReference):
                        lookup.resolve(self).usedin.add(chain_rule)
                    else:
                        lookup.usedin.add(chain_rule)
        self.doneUsageMarking = True

    def hoist_languages(self) -> None:
        """Sort routines into scripts and languages and resolve wildcards."""
        scripts: Dict[str, List[str]] = {}
        count = 0

        def add_language(pair: ScriptLanguage) -> None:
            nonlocal count
            script, lang = pair
            if lang == "*":
                return
            languages = scripts.setdefault(script, [])
            if lang not in languages:
                count = count + 1
                languages.append(lang)

        for k in self.routines:
            if k.languages:
                for lang in k.languages:
                    add_language(lang)
            else:
                for r in k.rules:
                    for lang in r.languages or []:
                        add_language(lang)

        # if count > 0 and not "DFLT" in scripts:
        #     scripts["DFLT"] = []
        #     scripts.move_to_end("DFLT", last=False)
        # if count > 0 and not "dflt" in scripts["DFLT"]:
        #     scripts["DFLT"].insert(0, "dflt")

        self.scripts_and_languages = scripts

    def hasScriptSupport(self, script: str) -> bool:
        """Check if the features object has support for a particular script.

        Args:
            script: A four-character OpenType script code.

        Returns:
            Whether the script is supported by these features.
        """
        self.hoist_languages()
        return script in self.scripts_and_languages

    def resolveAllRoutines(self) -> None:
        """Resolve reference use in chains.

        Checks that all routines referenced in chain rules can actually
        be found within the object, and adds pointers to match named routine
        references with the relevant :py:class:`Routine` object.
        """
        for routine in self.routines:
            for r in routine.rules:
                if not isinstance(r, Chaining):
                    continue
                for lookuplistIx in range(len(r.lookups)):
                    r.lookups[lookuplistIx] = self.ensureLookupsAreReferences(
                        r.lookups[lookuplistIx]
                    )

    def ensureLookupsAreReferences(
        self, lookuplist: Optional[Iterable[Lookup]]
    ) -> Optional[List[Lookup]]:
        """Ensures that all references are lookups.

        Naughty people might put :py:class:`Routine` objects directly into
        :py:class:`Chain` lookups. This tidies them up.
        """
        if not lookuplist:
            return None
        rv: List[Lookup] = []
        for r in lookuplist:
            if isinstance(r, RoutineReference):
                r.resolve(self)
                reference = r
            else:
                reference = self.referenceRoutine(r)
            assert reference.routine in self.routines
            rv.append(reference)
        return rv

    def setGlyphClassesFromFont(self, font: Any) -> None:
        """Loads glyph classes from the font.

        Args:
            font: Either a ``babelfont`` font object or a ``fontTools``
                ``TTFont``-like object with glyph category information.
        """
        for g in font.exported_glyphs():
            if hasattr(font, "glyphs"):
                self.glyphclasses[g] = font.glyphs[g].category
            else:
                self.glyphclasses[g] = font[g].category

    def partitionRoutine(
        self, routine: Routine, factor: Callable[[Rule], Any]
    ) -> List[Routine]:
        """Splits a routine based on a predicate.

        This method applies a function to each rule in the routine and creates
        distinct routines, each containing rules with the same return value
        from the function. This is useful, for example, when exporting to
        OpenType, to ensure that all rules in a routine must have the same type,
        same flags, etc.

        Args:
            routine: A :py:class:`Routine` object.
            factor: A function applied to each of the :py:class:`Rule` objects.

        Returns:
            A list of :py:class:`Routine` objects. The ``.routines`` list of the
            FontFeatures object is also modified in place.
        """
        if not routine.rules:
            return []
        self.doneUsageMarking = False
        self.markRoutineUseInChains()

        split_routines: Dict[Any, Tuple[Routine, List[Rule]]] = {}
        # The first rule stays in the original
        split_routines[factor(routine.rules[0])] = (routine, [routine.rules[0]])
        for rule in routine.rules[1:]:
            thisfactor = factor(rule)
            if thisfactor not in split_routines:
                rulelist: List[Rule] = []
                newroutine = copy(routine)
                newroutine.rules = rulelist
                split_routines[thisfactor] = (newroutine, rulelist)
            split_routines[thisfactor][1].append(rule)

        # Alter the first rule's routine's rulelist (we couldn't alter it on
        # the fly because we were iterating over it).
        routine_with_first_rule, rulelist = split_routines[factor(routine.rules[0])]
        routine_with_first_rule.rules = rulelist

        allroutines = [x[0] for x in split_routines.values()]
        return self.replaceRoutineWithSplitList(routine, allroutines)

    def replaceRoutineWithSplitList(
        self, routine: Routine, allroutines: List[Routine]
    ) -> List[Routine]:
        """Replace a routine with the routines it was split into.

        Args:
            routine: The original :py:class:`Routine` object.
            allroutines: The routines which replace it.

        Returns:
            The replacement routines.
        """
        self.markRoutineUseInChains()
        index = self.routines.index(routine)
        usedin = routine.usedin
        self.routines[index : index + 1] = allroutines
        for user in usedin:
            for ix, lookuplist in enumerate(user.lookups):
                if not lookuplist:
                    continue
                user.lookups[ix] = self._replaceRoutineInLookupList(
                    lookuplist, routine, allroutines
                )
        # Same trick for features
        for tag, lookuplist in self.features.items():
            self.features[tag] = cast(
                "List[RoutineReference]",
                self._replaceRoutineInLookupList(lookuplist, routine, allroutines),
            )
        return allroutines

    @staticmethod
    def _replaceRoutineInLookupList(
        lookuplist: Iterable[Lookup], routine: Routine, allroutines: List[Routine]
    ) -> List[Lookup]:
        """Replace references to a routine with a list of new routines.

        Args:
            lookuplist: The lookups to adjust.
            routine: The routine being replaced.
            allroutines: The routines which replace it.

        Returns:
            A new list of lookups with matching entries expanded.
        """
        newlist: List[Lookup] = []
        for lookup in lookuplist:
            if lookup == routine or (
                isinstance(lookup, RoutineReference) and lookup.routine == routine
            ):
                newlist.extend(RoutineReference(routine=r) for r in allroutines)
            else:
                newlist.append(lookup)
        return newlist

    from .feaLib.FontFeatures import asFea, asFeaAST
    from .xmlLib.FontFeatures import toXML, fromXML
    from .ttLib.FontFeatures import buildBinaryFeatures


class Routine:
    """Represent a Routine (similar to OT Lookup).

    A routine is a set of rules, sometimes but not always with an explicit name.
    It can apply to a set of language/script pairs.
    """

    def __init__(
        self,
        name: str = "",
        rules: Optional[List[Rule]] = None,
        address: Optional[Any] = None,
        inlined: bool = False,
        languages: Optional[List[ScriptLanguage]] = None,
        parent: Optional[FontFeatures] = None,
        flags: int = 0,
        markFilteringSet: Optional[Sequence[str]] = None,
        markAttachmentSet: Optional[Sequence[str]] = None,
    ) -> None:
        self.name = name
        self.usecount: int = 0
        self.usedin: Set[Chaining] = set()
        self._rules: List[Rule] = rules if rules is not None else []
        self.address = address
        self.comments: List[str] = []
        self.inlined = inlined
        self.languages: List[ScriptLanguage] = languages or []
        self.parent = parent
        self.flags = flags
        self.markFilteringSet = markFilteringSet
        self.markAttachmentSet = markAttachmentSet

    @property
    def rules(self) -> List[Rule]:
        """The rules contained in this routine."""
        return self._rules

    @rules.setter
    def rules(self, rules: List[Rule]) -> None:
        self._rules = rules

    def addRule(self, rule: Rule) -> None:
        """Adds a rule to a Routine.

        Args:
            rule: A ``Substitution``, ``Positioning``, etc. object.
        """
        assert isinstance(rule, Rule)
        self.rules.append(rule)

    def addComment(self, comment: str) -> None:
        """Adds a comment to a Routine.

        Comments are emitted when the Routine is converted to text formats
        such as AFDKO.

        Args:
            comment: A string comment.
        """
        self.comments.append(comment)

    @property
    def involved_glyphs(self) -> Set[str]:
        """Returns the names of all of the glyphs involved in this Routine."""
        return set().union(*(r.involved_glyphs for r in self.rules))

    @property
    def stage(self) -> Optional[str]:
        """Returns which shaping stage this routine is used in.

        Returns:
            ``sub`` for substitution stage, ``pos`` for positioning stage.
        """
        for r in self.rules:
            if isinstance(r, Substitution):
                return "sub"
            if isinstance(r, Positioning):
                return "pos"
            if isinstance(r, Attachment):
                return "pos"
            if isinstance(r, Chaining):
                return r.stage
        return None

    @property
    def dependencies(self) -> List[Routine]:
        """Returns a list of :py:class:`Routine` objects called as lookups in
        this Routine."""
        deps: List[Routine] = []
        for r in self.rules:
            deps.extend(r.dependencies)
        return deps

    from .feaLib.Routine import asFea, asFeaAST, feaPreamble
    from .shaperLib.Routine import apply_to_buffer
    from .xmlLib.Routine import toXML, fromXML
    from .ttLib.Routine import toOTLookup


class ExtensionRoutine(Routine):
    """OpenType-specific concept: A routine which contains other routines."""

    def __init__(self, routines: List[Routine], **kwargs: Any) -> None:
        self.routines = routines
        super().__init__(**kwargs)

    def apply_to_buffer(
        self,
        buf: Any,
        stage: Optional[str] = None,
        feature: Optional[str] = None,
        namedclasses: Optional[Mapping[str, Sequence[str]]] = None,
    ) -> None:
        """Applies shaping rules from this routine to a buffer.

        Args:
            buf: A :py:class:`fontFeatures.shaperLib.Buffer` object.
            stage: Shaping stage - ``sub`` or ``pos``.
            feature: The feature being processed. (For debugging.)
            namedclasses: A mapping of named glyph classes to glyph lists.

        Modifies the ``buf`` object.
        """
        for r in self.routines:
            r.apply_to_buffer(buf, stage, feature, namedclasses or {})

    def asFeaAST(self) -> Any:
        """Returns this extension routine as ``fontTools.feaLib.ast`` objects."""
        import fontTools.feaLib.ast as feaast

        f = feaast.Block()
        for r in self.routines:
            f.statements.append(r.asFeaAST())
        return f

    @property
    def stage(self) -> Optional[str]:
        """Returns which shaping stage this routine is used in.

        Returns:
            ``sub`` for substitution stage, ``pos`` for positioning stage.
        """
        return self.routines[0].stage

    @property
    def rules(self) -> List[Rule]:
        """All rules under this extension.

        Returns:
            A flattened list of :py:class:`Rule` objects.
        """
        return list(chain.from_iterable(routine.rules for routine in self.routines))

    @rules.setter
    def rules(self, rules: List[Rule]) -> None:
        """Does nothing. Don't set rules here."""


class RoutineReference:
    """A reference to a Routine object, used in a lookup.

    Routines can be referenced either by name (for example, when loaded from a
    textual representation), in which case they will be resolved at a later time,
    or by providing a pointer to the :py:class:`Routine` object.
    """

    #: The object which owns this rule, if any.
    parent: Optional[FontFeatures]

    def __init__(
        self, name: Optional[str] = None, routine: Optional[Routine] = None
    ) -> None:
        self.languages: List[ScriptLanguage] = []
        self.routine = routine
        self.name: Optional[str] = routine.name if routine is not None else None
        if name:
            self.name = name

    def resolve(self, ff: FontFeatures) -> Routine:
        """Resolves the reference in the context of a :py:class:`FontFeatures`
        object.

        Args:
            ff: The :py:class:`FontFeatures` object in which to look up the
                routine.

        Returns:
            The :py:class:`Routine` this reference points at.

        Raises:
            ValueError: If the named routine cannot be found.
        """
        routine = self.routine
        if routine is None:
            if self.name is None:
                raise ValueError("Cannot resolve a routine reference without a name")
            routine = ff.routineNamed(self.name)
            self.routine = routine
        if not self.name:
            self.name = routine.name
        return routine

    @property
    def stage(self) -> Optional[str]:
        """Returns which shaping stage this routine is used in.

        Returns:
            ``sub`` for substitution stage, ``pos`` for positioning stage.
        """
        if not self.routine:
            raise ValueError("Routine reference not resolved")
        return self.routine.stage

    from .xmlLib.RoutineReference import fromXML, toXML
    from .feaLib.RoutineReference import asFeaAST, feaPreamble

    def asFea(self) -> str:
        """Returns this Rule as a string of AFDKO feature text."""
        return self.asFeaAST().asFea()


class Rule:
    """A base class for all rules."""

    #: Glyph classes which must appear before the rule's input.
    precontext: GlyphClasses
    #: Glyph classes which must appear after the rule's input.
    postcontext: GlyphClasses
    #: The scripts and languages to which this rule applies.
    languages: Optional[List[ScriptLanguage]]
    #: Rules which call other routines (chains and substitutions) may have
    #: lookups to apply at each position of their input sequence.
    lookups: List[Optional[List[Lookup]]]
    #: The object which owns this rule, if any.
    parent: Optional[FontFeatures]

    def asFeaAST(self) -> Any:
        """Returns this rule as a ``fontTools.feaLib.ast`` statement."""
        raise NotImplementedError

    def asFea(self) -> str:
        """Returns this Rule as a string of AFDKO feature text."""
        return self.asFeaAST().asFea()

    def feaPreamble(self, ff: FontFeatures) -> List[Any]:
        """Computes any text that needs to go in the feature file header."""
        return []

    from .shaperLib.Rule import would_apply_at_position, pre_post_context_matches
    from .xmlLib.Rule import fromXML, toXML, _makeglyphslots, _slotArray

    @property
    def has_context(self) -> bool:
        """Does this rule have any pre- or post-context defined?"""
        return bool(len(self.precontext) or len(self.postcontext))

    @property
    def involved_glyphs(self) -> Set[str]:
        """Returns a set of all glyphs involved in this rule."""
        return set()

    @property
    def dependencies(self) -> List[Routine]:
        """Returns a list of :py:class:`Routine` objects called as lookups in
        this Routine."""
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
        force_alt: Force this substitution to be interpreted as an alternate
            substitution.

    Examples::

        lig = Substitution(
            [ ["f"], ["i"] ],
            ["f_i"]
        ) # sub f i by f_i;

        contextual = Substitution(
            [ ["dotbelow"] ],
            [ ["dotbelow.post"] ],
            precontext = [["ra-myanmar", "ra-myanmar.bt1", "ra-myanmar.bt2"]]
        ) # sub [ra-myanmar ra-myanmar.bt1 ra-myanmar.bt2] dotbelow-myanmar'
          # by dotbelow-myanmar.post;
    """

    def __init__(
        self,
        input_: GlyphClasses,
        replacement: GlyphClasses,
        precontext: Optional[GlyphClasses] = None,
        postcontext: Optional[GlyphClasses] = None,
        address: Optional[Any] = None,
        languages: Optional[List[ScriptLanguage]] = None,
        lookups: Optional[List[Optional[List[Lookup]]]] = None,
        reverse: bool = False,
        flags: int = 0,
        force_alt: bool = False,
    ) -> None:
        self.precontext = precontext or []
        self.postcontext = postcontext or []
        self.input = input_
        self.replacement = replacement
        self.address = address
        self.lookups = lookups or []
        self.languages = languages
        self.flags = flags
        self.reverse = reverse
        self.stage = "sub"
        self.force_alt = force_alt

    @property
    def involved_glyphs(self) -> Set[str]:
        """Returns a set of all glyphs involved in this rule."""
        i = set(chain.from_iterable(self.input))
        o = set(chain.from_iterable(self.replacement))
        b = set(chain.from_iterable(self.precontext))
        a = set(chain.from_iterable(self.postcontext))
        return i | o | b | a

    from .feaLib.Substitution import asFeaAST
    from .shaperLib.Substitution import shaper_inputs, _do_apply
    from .xmlLib.Substitution import _toXML, fromXML
    from .ttLib.Substitution import lookup_type


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

    Example::

        sub_Qu = Routine(rules=[
            Substitute([["Q"]], [["Q.beforeu"]])
        ])

        chain = Chain(
            [["Q"]],
            postcontext = [ ["u", "v", "u.sc", "v.sc"] ],
            lookups = [ [sub_Qu] ]
        ) # sub Q' lookup sub_Qu [u v u.sc v.sc];
    """

    def __init__(
        self,
        input_: GlyphClasses,
        precontext: Optional[GlyphClasses] = None,
        postcontext: Optional[GlyphClasses] = None,
        address: Optional[Any] = None,
        languages: Optional[List[ScriptLanguage]] = None,
        lookups: Optional[List[Optional[List[Lookup]]]] = None,
        flags: int = 0,
    ) -> None:
        self.precontext = precontext or []
        self.postcontext = postcontext or []
        self.input = input_
        self.address = address
        self.lookups = lookups or []
        self.languages = languages
        self.flags = flags

    @property
    def stage(self) -> Optional[str]:
        """Returns which shaping stage this routine is used in.

        Returns:
            ``sub`` for substitution stage, ``pos`` for positioning stage.
        """
        for lookuplist in self.lookups:
            if not lookuplist:
                continue
            for aLookup in lookuplist:
                if not aLookup:
                    continue
                return aLookup.stage
        return None

    @property
    def involved_glyphs(self) -> Set[str]:
        """Returns a set of all glyphs involved in this rule."""
        i = set(chain.from_iterable(self.input))
        b = set(chain.from_iterable(self.precontext))
        a = set(chain.from_iterable(self.postcontext))
        return i | b | a

    @property
    def dependencies(self) -> List[Routine]:
        """Returns a list of :py:class:`Routine` objects called as lookups in
        this Routine."""
        deps: List[Routine] = []
        for lookuplist in self.lookups:
            for aLookup in lookuplist or []:
                if isinstance(aLookup, RoutineReference):
                    assert aLookup.routine is not None
                    deps.append(aLookup.routine)
                else:
                    deps.append(aLookup)
        return deps

    from .feaLib.Chaining import asFeaAST, feaPreamble
    from .shaperLib.Chaining import shaper_inputs, _do_apply
    from .xmlLib.Chaining import _toXML, fromXML
    from .ttLib.Chaining import lookup_type


class ValueRecord(feaLibValueRecord):
    """A value record for representing positional changes in advance and placement.

    See :py:class:`fontTools.feaLib.ValueRecord`, from which this inherits.
    """

    from .ttLib.ValueRecord import toOTValueRecord

    @property
    def is_variable(self) -> bool:
        """Returns true if any of the elements of the value record are a
        :py:class:`fontTools.feaLib.VariableScalar`."""
        return any(
            isinstance(x, VariableScalar)
            for x in [
                self.xPlacement,
                self.yPlacement,
                self.xAdvance,
                self.yAdvance,
            ]
        )


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

    Example::

        open_up_behs = Positioning(
            [
                ["BEi1", "BEi2"],
                ["sda", "sdb", "dda", "ddb"]
            ],
            [
                ValueRecord(xAdvance=200),
                ValueRecord(xPlacement=50),
            ]
            postcontext = [ medis_finas ]
        )
        # pos [BEi1 BEi2]' <0 0 200 0> [sda sdb dda ddb]' <0 50 0 0> @medis_finas;
    """

    def __init__(
        self,
        glyphs: GlyphClasses,
        valuerecords: Sequence[ValueRecord],
        precontext: Optional[GlyphClasses] = None,
        postcontext: Optional[GlyphClasses] = None,
        address: Optional[Any] = None,
        languages: Optional[List[ScriptLanguage]] = None,
        flags: int = 0,
    ) -> None:
        self.precontext = precontext or []
        self.postcontext = postcontext or []
        assert len(glyphs) == len(valuerecords)
        self.glyphs = glyphs
        self.valuerecords = valuerecords
        self.address = address
        self.languages = languages
        self.flags = flags
        self.stage = "pos"

    @property
    def involved_glyphs(self) -> Set[str]:
        """Returns a set of all glyphs involved in this rule."""
        i = set(chain.from_iterable(self.glyphs))
        b = set(chain.from_iterable(self.precontext))
        a = set(chain.from_iterable(self.postcontext))
        return i | b | a

    from .feaLib.Positioning import asFeaAST
    from .shaperLib.Positioning import shaper_inputs, _do_apply
    from .xmlLib.Positioning import _toXML, fromXML
    from .ttLib.Positioning import lookup_type


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
        force_markmark: boolean. If true, force this to be interpreted as a
            mark-to-mark operation

    Whether this is a mark-to-base or mark-to-mark operation will be determined
    by the glyph category of the glyphs involved in the `bases` dictionary and
    the value of the `force_markmark` argument.

    Examples::

        ff.anchors = {
            "a": { "top": (250, 603) },
            "acutecomb": { "_top": (56, 0) }
        }

        top_bases = {}
        top_marks = {}
        for glyphname, anchors in ff.anchors.items():
            for anchorname, position in anchors.items():
                if anchorname == "top":
                    top_bases[glyphname] = position
                if anchorname == "_top":
                    top_marks[glyphname] = position

        # top_bases = { "a": (260,603) }
        # top_marks = { "acutecomb": (56,0) }

        tops = Attachment("top", "_top", top_bases, top_marks)
    """

    def __init__(
        self,
        base_name: str,
        mark_name: str,
        bases: Optional[Dict[str, AnchorPosition]] = None,
        marks: Optional[Dict[str, AnchorPosition]] = None,
        fullname: Optional[str] = None,
        flags: int = 0,
        address: Optional[Any] = None,
        font: Optional[Any] = None,
        languages: Optional[List[ScriptLanguage]] = None,
        force_markmark: bool = False,
    ) -> None:
        self.base_name = base_name
        self.mark_name = mark_name
        self.fullname = fullname or (self.base_name + "_" + self.mark_name)
        self.bases = bases or {}
        self.marks = marks or {}
        self.flags = flags
        self.address = address
        self.font = font
        self.stage = "pos"
        self.languages = languages or []
        self.force_markmark = force_markmark

    @property
    def is_cursive(self) -> bool:
        """Returns true if this is a cursive attachment rule."""
        return self.base_name == "cursive_entry" or self.base_name == "entry"  # XXX

    from .feaLib.Attachment import asFeaAST, feaPreamble
    from .shaperLib.Attachment import shaper_inputs, _do_apply, would_apply_at_position
    from .xmlLib.Attachment import _toXML, fromXML
    from .ttLib.Attachment import lookup_type

    @property
    def involved_glyphs(self) -> Set[str]:
        """Returns a set of all glyphs involved in this rule."""
        b = set(self.bases.keys())
        m = set(self.marks.keys())
        return b | m
