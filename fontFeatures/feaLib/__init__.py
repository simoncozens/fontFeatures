import io
import fontFeatures

class FeaUnparser():
    def __init__(self, featurefile, font = None):
        from fontTools.feaLib.parser import Parser
        self.ff = fontFeatures.FontFeatures()
        glyphmap = ()
        if font:
            glyphmap = font.getReverseGlyphMap()
        if isinstance(featurefile, str):
            featurefile = io.StringIO(featurefile)
        parsetree = Parser(featurefile, glyphmap).parse()
        self.features_ = {}
        parsetree.build(self)

    def find_named_routine(self, name):
        candidates = list(filter(lambda x:x.name==name, self.ff.routines))
        if not candidates:
            raise ValueError("Reference to undefined routine "+name)
        if len(candidates) > 1:
            raise ValueError("This can't happen")
        return candidates[0]

    def start_lookup_block(self, location, name):
        location = "%s:%i:%i" % (location)
        self.currentRoutine = fontFeatures.Routine(name=name, address=location)
        self.ff.addRoutine(self.currentRoutine)

    def start_feature(self, location, name):
        location = "%s:%i:%i" % (location)
        self.currentRoutine = fontFeatures.Routine(address=location)
        self.ff.addFeature(name, [self.currentRoutine])

    def add_single_subst(self, location, prefix, suffix, mapping, forceChain):
        location = "%s:%i:%i" % (location)
        s = fontFeatures.Substitution(
            input_ = [ list(mapping.keys()) ],
            replacement = [ list(mapping.values()) ],
            precontext = prefix,
            postcontext = suffix,
            address = location
        )
        self.currentRoutine.addRule(s)

    def add_multiple_subst(self, location, prefix, glyph, suffix, replacements, forceChain):
        location = "%s:%i:%i" % (location)
        s = fontFeatures.Substitution(
            input_ = [ [glyph] ],
            replacement = [ [g] for g in replacements ],
            precontext = prefix,
            postcontext = suffix,
            address = location
        )
        self.currentRoutine.addRule(s)

    def add_alternate_subst(self, location,
                            prefix, glyph, suffix, replacement):
        location = "%s:%i:%i" % (location)
        s = fontFeatures.Substitution(
            input_ = [ [glyph] ],
            replacement = [ replacement ],
            precontext = prefix,
            postcontext = suffix,
            address = location
        )
        self.currentRoutine.addRule(s)

    def add_ligature_subst(self, location,
                           prefix, glyphs, suffix, replacement, forceChain):
        location = "%s:%i:%i" % (location)
        s = fontFeatures.Substitution(
            input_ = [list(x) for x in glyphs],
            replacement = [[ replacement ]],
            precontext = prefix,
            postcontext = suffix,
            address = location
        )
        self.currentRoutine.addRule(s)

    def add_chain_context_subst(self, location, prefix, glyphs, suffix, lookups):
        location = "%s:%i:%i" % (location)
        # Find named feature
        lookups = [ [self.find_named_routine(x.name)] for x in lookups]
        s = fontFeatures.Chaining(
            input_ = [list(x) for x in glyphs],
            precontext = prefix,
            postcontext = suffix,
            lookups = lookups,
            address = location
        )
        self.currentRoutine.addRule(s)

    def end_lookup_block(self):
        pass

    def end_feature(self):
        pass
