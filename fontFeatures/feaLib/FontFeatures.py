# Code for converting a FontFeatures object into feaLib statements
import fontTools.feaLib.ast as feaast
import itertools
from fontFeatures.feaLib.Routine import lookup_type


def add_language_system_statements(self, ff):
    self.hoist_languages()

    total_languages = sum([len(x) for x in self.scripts_and_languages.values()])

    if total_languages < 2:
        return
    for s, entry in self.scripts_and_languages.items():
        for l in entry:
            ff.statements.append(feaast.LanguageSystemStatement(s, l))


def asFea(self,**kwargs):
    return self.asFeaAST(**kwargs).asFea()


def _to_inline_class(glyphs):
    return feaast.GlyphClass([feaast.GlyphName(x) for x in glyphs])


def reorderAndResolve(self):
    from fontFeatures import Chaining

    # Arrange the routines based on dependencies

    # First pass ensures all are references and resolves them. We do this in
    # two passes because if any bare Routines got in there, they're going to
    # to be added to the end of the routine list.
    self.resolveAllRoutines()

    # Second pass reorders
    ordering = list(range(0, len(self.routines)))
    ptr = len(self.routines) - 1
    while ptr >= 0:
        routine = self.routines[ptr]
        if not any(isinstance(r, Chaining) for r in routine.rules):
            ptr = ptr - 1
            continue

        later = []
        for r in routine.rules:
            for lookuplist in r.lookups:
                if not lookuplist:
                    continue
                for lookup in lookuplist:
                    lookup.routine.usecount = (
                        999  # Always explicitly list referenced lookups
                    )
                    ix = self.routines.index(lookup.routine)
                    if ix > ptr:
                        later.append(ix)
        for ix in later:
            f = ordering.pop(ordering.index(ix))
            ordering.insert(ptr, f)
        ptr = ptr - 1
    return ordering


def asFeaAST(self, do_gdef=True):
    """Returns this font's features as a feaLib AST object, for later
    translation to AFDKO code."""
    from fontFeatures import Routine, Chaining

    ff = feaast.FeatureFile()

    add_language_system_statements(self, ff)

    if do_gdef:
        add_gdef(self, ff)

    # In OpenType, we need to rearrange the routines such that all rules for
    # a given languagesystem, lookup type, and lookup flags, appear in the
    # same lookup. Also, lookups with the same languagesystem need to appear next
    # to one another, because FEA syntax is stupid.

    # Now arrange them by type/etc.
    for k,v in self.features.items():
        for reference in v:
            routine = reference.routine
            self.partitionRoutine(routine,
                lambda rule:
                    tuple([tuple(rule.languages or []),
                    type(rule),
                    lookup_type(rule)
                    ])
            )
    for r in self.routines:
        r.usecount = 0
        # Bubble up flags
        r.flags = r.rules[0].flags
    for k, v in self.features.items():
        for reference in v:
            routine = reference.routine
            routine.languages = routine.rules[0].languages
            routine.usecount += 1
        # Order the arranged routines by language
        new_references = list(sorted(v, key=lambda x: tuple(x.routine.languages or [])))
        # Bubble up flags
        self.features[k] = new_references

    # Next, we'll ensure that all chaining lookups are resolved and in the right order
    newRoutines = [self.routines[i] for i in reorderAndResolve(self)]


    # Preamble
    for k in newRoutines:
        assert isinstance(k, Routine)
        if not k.name and k.usecount != 1:
            k.name = self.gensym("Routine_")
        pre = k.feaPreamble(self)
        if k.rules:
            ff.statements.extend(pre)

    for k, v in self.namedClasses.items():
        asclass = _to_inline_class(v)
        ff.statements.append(feaast.GlyphClassDefinition(k, asclass))

    ff.statements.append(feaast.Comment(""))

    for k in newRoutines:
        if k.rules and k.usecount != 1:
            ff.statements.append(k.asFeaAST())

    for k, v in self.features.items():
        f = feaast.FeatureBlock(k)
        last_langsys = ("DFLT", "dflt")
        for routine in v:
            if routine.routine.languages and routine.routine.languages[0] != last_langsys:
                new_langsys = routine.routine.languages[0]
                if new_langsys[0] != last_langsys[0]:
                    f.statements.append(feaast.ScriptStatement(new_langsys[0]))
                if new_langsys[1] != last_langsys[1]:
                    f.statements.append(feaast.LanguageStatement("%4s" % new_langsys[1]))
                last_langsys = new_langsys
            f.statements.append(routine.asFeaAST(expand = k=="aalt"))
        ff.statements.append(f)
    return ff


def add_gdef(self, ff):
    gdef = feaast.TableBlock("GDEF")
    gc = self.glyphclasses
    categories = {"base": [], "mark": [], "ligature": [], "component": []}
    for k, v in gc.items():
        categories[v] = categories.get(v, []) + [k]
    if categories:
        gdef.statements.append(
            feaast.GlyphClassDefStatement(
                _to_inline_class(categories["base"]),
                _to_inline_class(categories["mark"]),
                _to_inline_class(categories["ligature"]),
                _to_inline_class(categories["component"]),
            )
        )
        ff.statements.append(gdef)
