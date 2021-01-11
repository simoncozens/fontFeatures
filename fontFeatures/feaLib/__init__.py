import io
import fontFeatures


class FeaUnparser:
    """Turns a AFDKO feature file or string into a FontFeatures object.

    Args:
        featurefile: File object or string.
        font: Optionally, a TTFont object.

    Returns:
        An object with a ``ff`` property, which is the ``FontFeatures`` object
        containing the rules of this file.
    """
    def __init__(self, featurefile, font=None):
        from fontTools.feaLib.parser import Parser

        self.ff = fontFeatures.FontFeatures()
        self.markclasses = {}
        self.currentFeature = None
        self.currentRoutine = None
        self.gensym = 1
        self.language_systems = []
        glyphmap = ()
        if font:
            glyphmap = font.getReverseGlyphMap()
        if isinstance(featurefile, str):
            featurefile = io.StringIO(featurefile)
        parsetree = Parser(featurefile, glyphmap).parse()
        self.features_ = {}
        parsetree.build(self)

    def find_named_routine(self, name):
        candidates = list(filter(lambda x: x.name == name, self.ff.routines))
        if not candidates:
            raise ValueError("Reference to undefined routine " + name)
        if len(candidates) > 1:
            raise ValueError("This can't happen")
        return candidates[0]

    def _start_routine_if_necessary(self, location):
        if not self.currentRoutine:
            self._start_routine(location, "")

    def _start_routine(self, location, name):
        location = "%s:%i:%i" % (location)
        # print("Starting routine at "+location)
        self._discard_empty_routine()
        self.currentRoutine = fontFeatures.Routine(name=name, address=location)
        if not name:
            self.currentRoutine.name = "unnamed_routine_%i" % self.gensym
            self.gensym = self.gensym + 1
        self.currentRoutineFlag = 0
        if self.currentFeature:
            reference = self.ff.referenceRoutine(self.currentRoutine)
            self.ff.addFeature(self.currentFeature, [reference])
        else:
            self.ff.routines.append(self.currentRoutine)

    def start_lookup_block(self, location, name):
        self._start_routine(location, name)

    def start_feature(self, location, name):
        self.currentFeature = name

    def set_font_revision(self, location, revision):
        pass

    def set_script(self, location, script):
        pass

    def add_single_subst(self, location, prefix, suffix, mapping, forceChain):
        self._start_routine_if_necessary(location)
        location = "%s:%i:%i" % (location)
        s = fontFeatures.Substitution(
            input_=[list(mapping.keys())],
            replacement=[list(mapping.values())],
            precontext=prefix,
            postcontext=suffix,
            address=location,
        )
        self.currentRoutine.addRule(s)

    def add_multiple_subst(
        self, location, prefix, glyph, suffix, replacements, forceChain
    ):
        self._start_routine_if_necessary(location)
        location = "%s:%i:%i" % (location)
        s = fontFeatures.Substitution(
            input_=[[glyph]],
            replacement=[[g] for g in replacements],
            precontext=prefix,
            postcontext=suffix,
            address=location,
        )
        self.currentRoutine.addRule(s)

    def add_alternate_subst(self, location, prefix, glyph, suffix, replacement):
        location = "%s:%i:%i" % (location)
        s = fontFeatures.Substitution(
            input_=[[glyph]],
            replacement=[replacement],
            precontext=prefix,
            postcontext=suffix,
            address=location,
        )
        self.currentRoutine.addRule(s)

    def add_ligature_subst(
        self, location, prefix, glyphs, suffix, replacement, forceChain
    ):
        location = "%s:%i:%i" % (location)
        s = fontFeatures.Substitution(
            input_=[list(x) for x in glyphs],
            replacement=[[replacement]],
            precontext=prefix,
            postcontext=suffix,
            address=location,
        )
        self.currentRoutine.addRule(s)

    def add_chain_context_subst(self, location, prefix, glyphs, suffix, lookups):
        location = "%s:%i:%i" % (location)
        # Find named feature
        mylookups = []
        for x in lookups:
            if x:
                mylookups.append([self.find_named_routine(y.name) for y in x])
            else:
                mylookups.append(None)
        s = fontFeatures.Chaining(
            input_=[list(x) for x in glyphs],
            precontext=prefix,
            postcontext=suffix,
            lookups=mylookups,
            address=location,
        )
        self.currentRoutine.addRule(s)

    def add_single_pos(self, location, prefix, suffix, pos, forceChain):
        location = "%s:%i:%i" % (location)
        s = fontFeatures.Positioning(
            glyphs=[p[0] for p in pos],
            valuerecords=[p[1] for p in pos],
            precontext=prefix,
            postcontext=suffix,
            address=location,
        )
        self.currentRoutine.addRule(s)

    def add_specific_pair_pos(self, location, glyph1, value1, glyph2, value2):
        location = "%s:%i:%i" % (location)
        s = fontFeatures.Positioning(
            glyphs=[[glyph1], [glyph2]], valuerecords=[value1, value2], address=location
        )
        self.currentRoutine.addRule(s)

    def add_class_pair_pos(self, location, glyphclass1, value1, glyphclass2, value2):
        location = "%s:%i:%i" % (location)
        s = fontFeatures.Positioning(
            glyphs=[glyphclass1, glyphclass2],
            valuerecords=[value1, value2],
            address=location,
        )
        self.currentRoutine.addRule(s)

    def add_cursive_pos(self, location, glyphclass, entryAnchor, exitAnchor):
        location = "%s:%i:%i" % (location)
        basedict, markdict = {}, {}
        if entryAnchor:
            basedict = {g: (entryAnchor.x, entryAnchor.y) for g in glyphclass}
        if exitAnchor:
            markdict = {g: (exitAnchor.x, exitAnchor.y) for g in glyphclass}
        s = fontFeatures.Attachment(
            base_name="cursive_entry",
            mark_name="cursive_exit",
            bases=basedict,
            marks=markdict,
            address=location,
        )
        self.currentRoutine.addRule(s)

    def add_mark_base_pos(self, location, bases, marks):
        location = "%s:%i:%i" % (location)
        for baseanchor, markclass in marks:
            assert len(markclass.definitions) == 1
            markanchor = markclass.definitions[0].anchor
            s = fontFeatures.Attachment(
                base_name=markclass.name,
                mark_name=markclass.name,
                bases={g: (baseanchor.x, baseanchor.y) for g in bases},
                marks={
                    g: (markanchor.x, markanchor.y) for g in markclass.glyphs.keys()
                },
                address=location,
            )
        self.currentRoutine.addRule(s)

    def set_lookup_flag(self, location, value, markAttach, markFilter):
        # If we're mid-feature, start a new routine here
        if self.currentFeature:
            self.end_lookup_block()
            self._discard_empty_routine()
            self._start_routine(location, None)
        self.currentRoutineFlag = value

    def add_language_system(self, location, script, language):
        self.language_systems.append((script, language))

    def add_lookup_call(self, lookup_name):

        routine = self.find_named_routine(lookup_name)
        if self.currentFeature:
            self._discard_empty_routine()
            self.ff.addFeature(self.currentFeature, [routine])
        else:
            raise ValueError("Huh?")

    def end_lookup_block(self):
        if self.currentRoutine:
            for rule in self.currentRoutine.rules:
                rule.flags = self.currentRoutineFlag

    def end_feature(self):
        self._discard_empty_routine()
        self.currentFeature = None
        for rule in self.currentRoutine.rules:
            rule.flags = self.currentRoutineFlag

    def _discard_empty_routine(self):
        if not self.currentFeature:
            return
        if self.currentRoutine and not self.currentRoutine.rules:
            if self.currentRoutine not in  self.ff.routines:
                # print("%s escaped!" % self.currentRoutine.name)
                return
            del(self.ff.routines[self.ff.routines.index(self.currentRoutine)])
            if self.currentFeature in self.ff.features:
                del(self.ff.features[self.currentFeature][-1])
        pass
