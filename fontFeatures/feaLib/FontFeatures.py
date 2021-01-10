# Code for converting a FontFeatures object into feaLib statements
import fontTools.feaLib.ast as feaast


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


def asFeaAST(self):
    """Returns this font's features as a feaLib AST object, for later
  translation to AFDKO code."""
    from fontFeatures import Routine

    ff = feaast.FeatureFile()

    add_language_system_statements(self, ff)

    # Preamble
    for k in self.routines:
        assert isinstance(k, Routine)
        if not k.name:
            k.name = self.gensym("Routine_")
        pre = k.feaPreamble(self)
        if k.rules:
            ff.statements.extend(pre)
    # for k, v in self.features.items():
    #     for r in v:
    #         pre = r.feaPreamble(self)
    #         for s in pre:
    #             ff.statements.append(s)

    # for k, v in self.namedClasses.items():
    #     asclass = feaast.GlyphClass([feaast.GlyphName(x) for x in v])
    #     ff.statements.append(feaast.GlyphClassDefinition(k, asclass))

    ff.statements.append(feaast.Comment(""))

    for k in self.routines:
        if k.rules:
            ff.statements.append(k.asFeaAST())

    for k, v in self.features.items():
        f = feaast.FeatureBlock(k)
        for n in v:
            f.statements.append(n.asFeaAST())
        ff.statements.append(f)
    return ff
