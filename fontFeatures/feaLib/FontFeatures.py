# Code for converting a FontFeatures object into feaLib statements
import fontTools.feaLib.ast as feaast
import itertools


def add_language_system_statements(self, ff):
    self.hoist_languages()
    if len(self.scripts_and_languages.keys()) == 0:
        return
    if len(self.scripts_and_languages.keys()) == 1:
        return
    for s, entry in self.scripts_and_languages.items():
        for l in entry:
            ff.statements.append(feaast.LanguageSystemStatement(s, l))


def asFea(self):
    return self.asFeaAST().asFea()


def reorderAndResolve(self):
    from fontFeatures import Chaining
    # Arrange the routines based on dependencies

    # First pass ensures all are references and resolves them. We do this in
    # two passes because if any bare Routines got in there, they're going to
    # to be added to the end of the routine list.
    self.resolveAllRoutines()

    # Second pass reorders
    ordering = list(range(0,len(self.routines)))
    ptr = len(self.routines)-1
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
                    lookup.routine.usecount = 999 # Always explicitly list referenced lookups
                    ix = self.routines.index(lookup.routine)
                    if ix > ptr:
                        later.append(ix)
        for ix in later:
            f = ordering.pop(ordering.index(ix))
            ordering.insert(ptr, f)
        ptr = ptr - 1
    return ordering

def asFeaAST(self):
    """Returns this font's features as a feaLib AST object, for later
  translation to AFDKO code."""
    from fontFeatures import Routine, Chaining

    ff = feaast.FeatureFile()

    add_language_system_statements(self, ff)

    newRoutines = [ self.routines[i] for i in reorderAndResolve(self) ]

    # Preamble
    for k in newRoutines:
        assert isinstance(k, Routine)
        if not k.name:
            k.name = self.gensym("Routine_")
        pre = k.feaPreamble(self)
        if k.rules:
            ff.statements.extend(pre)

    for k, v in self.namedClasses.items():
        asclass = feaast.GlyphClass([feaast.GlyphName(x) for x in v])
        ff.statements.append(feaast.GlyphClassDefinition(k, asclass))


    ff.statements.append(feaast.Comment(""))

    for k in newRoutines:
        if k.rules and k.usecount != 1:
            ff.statements.append(k.asFeaAST())

    expandedLanguages = []
    for s,ls in self.scripts_and_languages.items():
        for l in ls:
            expandedLanguages.append((s,l))
    for k, v in self.features.items():
        f = feaast.FeatureBlock(k)
        for n in v:
            f.statements.append(n.asFeaAST(allLanguages=expandedLanguages))
        ff.statements.append(f)
    return ff
