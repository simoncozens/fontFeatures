# Code for converting a Routine object into feaLib statements
import fontTools.feaLib.ast as feaast
from fontFeatures.ttLib.Substitution import lookup_type as sub_lookup_type
from fontFeatures.ttLib.Positioning import lookup_type as pos_lookup_type


def lookup_type(rule):
    from fontFeatures import Substitution, Positioning, Attachment, Chaining

    if isinstance(rule, Substitution):
        return sub_lookup_type(rule)
    if isinstance(rule, Positioning):
        return pos_lookup_type(rule)
    if isinstance(rule, Attachment):
        return rule.is_cursive
    if isinstance(rule, Chaining):
        return 1
    raise ValueError


counter = 0


def gensym(prefix):
    global counter
    counter = counter + 1
    return prefix + str(counter)


def arrange_by_type(self):
    from fontFeatures import Routine

    # Arrange into rules of similar type (Substitution/Positioning)
    ruleTypes = {}
    for r in self.rules:
        if not type(r) in ruleTypes:
            ruleTypes[type(r)] = []
        ruleTypes[type(r)].append(r)
    if len(ruleTypes.keys()) == 1:
        return
    routines = []
    for k, v in ruleTypes.items():
        r = Routine(rules=v, flags=self.flags)
        if self.name:
            r.name = self.name + "_" + str(k)
    return routines


# A lookup in OpenType can only contain rules of the same lookup type
def arrange_by_lookup_type(self):
    from fontFeatures import Routine

    ruleTypes = {}
    for r in self.rules:
        if not lookup_type(r) in ruleTypes:
            ruleTypes[lookup_type(r)] = []
        ruleTypes[lookup_type(r)].append(r)
    if len(ruleTypes.keys()) == 1:
        return
    # Special case the fact that a single sub can be expressed as part of a
    # multiple sub if needed
    if tuple(sorted(ruleTypes.keys())) == (1, 2) or tuple(sorted(ruleTypes.keys())) == (1, 8):
        return
    routines = []
    for k, v in ruleTypes.items():
        r = Routine(rules=v, flags=self.flags)
        if self.name:
            r.name = self.name + "_" + str(k)
        routines.append(r)
    return routines


# A lookup in OpenType can only have one flag
def arrange_by_flags(self):
    from fontFeatures import Routine

    flagTypes = {}
    for r in self.rules:
        if not r.flags in flagTypes:
            flagTypes[r.flags] = []
        flagTypes[r.flags].append(r)
    if len(flagTypes.keys()) == 1:
        if not self.flags:
            self.flags = 0
        self.flags = self.flags | list(flagTypes.keys())[0]
        return
    routines = []
    for k, v in flagTypes.items():
        r = Routine(rules=v, flags=k)
        if self.name:
            r.name = self.name + "_" + str(k)
        routines.append(r)
    return routines


def arrange_by_language(self):
    from fontFeatures import Routine

    if not self.languages:
        return
    languages = {}

    def add_lang(p, r):
        nonlocal languages
        if not p in languages:
            languages[p] = []
        languages[p].extend(r)

    for s, l in self.languages:
        if l == "*":
            add_lang((s, "dflt"), self.rules)
        else:
            add_lang((s, l), self.rules)

    if len(languages.keys()) < 2:
        return
    routines = []
    for k, v in languages.items():
        r = Routine(rules=v, languages=[k], flags=self.flags)
        if self.name:
            r.name = self.name + "_" + k[0] + "_" + k[1]
        routines.append(r)
    return routines


def arrange(self):
    splitType = arrange_by_type(self)
    if splitType:
        return splitType
    splitType = arrange_by_lookup_type(self)
    if splitType:
        return splitType
    splitLang = arrange_by_language(self)
    if splitLang:
        return splitLang
    splitFlags = arrange_by_flags(self)
    if splitFlags:
        return splitFlags
    return None


def feaPreamble(self, ff):
    preamble = []
    for r in self.rules:
        preamble.extend(r.feaPreamble(ff))
    if hasattr(self, "markFilteringSet"):
        self.markFilteringSetAsClass = ff.getNamedClassFor(self.markFilteringSet, gensym("markFilteringSet"))
    return preamble


def asFeaAST(self):
    if self.name:
        f = feaast.LookupBlock(name=self.name)
    else:
        f = feaast.Block()

    arranged = arrange(self)

    if arranged:
        for a in arranged:
            f.statements.append(asFeaAST(a))
        return f

    if self.languages and not (
        self.languages[0][0] == "DFLT" and self.languages[0][1] == "dflt"
    ):
        s, l = self.languages[0]
        f.statements.append(feaast.ScriptStatement(s))
        if l != "*":
            l = "%4s" % l
            f.statements.append(feaast.LanguageStatement(l))

    if hasattr(self, "flags") and self.flags > 0:
        if self.flags & 0xFF00:
            # This is dirty and wrong and I feel bad.
            flags = feaast.LookupFlagStatement(
                self.flags,
                markAttachment=feaast.Comment("@MarkClass%i" % (self.flags >> 8)),
            )
        else:
            flags = feaast.LookupFlagStatement(self.flags)
        if hasattr(self, "markFilteringSetAsClass"):
            # We only need the name, not the contents
            mfs = feaast.GlyphClassDefinition(self.markFilteringSetAsClass,
                feaast.GlyphClass([])
            )
            flags.markFilteringSet = feaast.GlyphClassName(mfs)
        f.statements.append(flags)

    for x in self.comments:
        f.statements.append(Comment(x))

    lastaddress = None
    for x in self.rules:
        if x.address and x.address != lastaddress:
            f.statements.append(feaast.Comment("# Original source: %s " % x.address))
            lastaddress = x.address
        f.statements.append(x.asFeaAST())
    return f


def asFea(self):
    return self.asFeaAST().asFea()
