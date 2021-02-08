import itertools
import fontFeatures
from fontFeatures.ttLib.GSUBUnparser import GSUBUnparser
from fontFeatures.ttLib import unparseLanguageSystems
from fontFeatures import FontFeatures
from argparse import ArgumentParser
from fontTools.ttLib import TTFont
from fontTools.subset import Options


class FontGlyphs:
    def __init__(self, ttFont):
        """
        Generate glyph inputs for a particular combination of script, lang,
        and features e.g:

        | >>> glyph_inputs = FontGlyphs(ttFont)
        | >>> glyph_inputs.inputs(script="dev2", lang="HIN ", features=[])
        [{
            'dvJ_J_NYA': {'features': {'half', 'akhn', 'pres'}, 'input': 'ज्ज्ञ'}
            ...
        }]

        This object is an improved version of notools.HBInput
        https://github.com/googlefonts/nototools/blob/master/nototools/hb_input.py
        """
        self.ttFont = ttFont
        self.unparsed = self._unparse_gsub()
        self.processed_lookups = set()
        self.glyph_inputs = self._get_encoded_glyphs()
        # We enable these features by default since most text-processing clients
        # do the same. If we don't enable these features, many scripts won't
        # work correctly e.g Arabic requires the init, medi and fina features
        # enabled by default.
        # Taken from pyftsubset:
        # https://github.com/fonttools/fonttools/blob/master/Lib/fontTools/subset/__init__.py#L2380
        self.dflt_features = Options._layout_features_default

    def inputs(
        self, script="DFLT", lang="dflt", features=[], include_default_features=True
    ):
        """
        Get all glyph inputs for a particular combination of script, lang
        and features.

        Args:
            script: String. An OpenType script tag e.g "arab"
            lang: String. An OpenType language tag e.g "MOL "
            features: A list containing OpenType features
            include_default_features: Bool. If False, default features will
                be disabled.

        script tag info:
        https://docs.microsoft.com/en-us/typography/opentype/spec/scripttags

        lang tag info:
        https://docs.microsoft.com/en-us/typography/opentype/spec/languagetags
        """
        if include_default_features:
            enabled_features = self.dflt_features + features
        else:
            enabled_features = features

        active_lookups = self._active_lookups(script, lang, enabled_features)

        for tag, routine in active_lookups:
            self._process_routine(tag, routine)

    def _unparse_gsub(self):
        # TODO (Marc F) cleanup this copy pasta
        languageSystems = unparseLanguageSystems([self.ttFont["GSUB"]])
        ff = FontFeatures()
        unparsed = GSUBUnparser(
            self.ttFont["GSUB"], ff, languageSystems, font=self.ttFont, config={}
        )
        unparsed.unparse(doLookups=True)
        return unparsed

    def _get_encoded_glyphs(self):
        inputs = {}
        for k, v in self.ttFont.getBestCmap().items():
            inputs[v] = {"input": chr(k), "features": set()}
        return inputs

    def _active_lookups(self, script, lang, selected_features):
        # Return a list of lookups which belong to the specific script, lang
        # and selected_features combination.

        # The idea is to mimmic the steps a text-processing client would take
        # if a user enabled a set of OT features for a selected block of
        # text. Details of the steps can be found here:
        # https://docs.microsoft.com/en-us/typography/opentype/spec/gsub#table-organization

        lookups = []
        # assign DFLT to script if selected script does not exist
        # assign dflt to lang if selected lang does not exist
        if script not in self.unparsed.languageSystems:
            script = "DFLT"
        if lang not in self.unparsed.languageSystems[script]:
            lang = "dflt"

        for feat in self.unparsed.features:
            if feat not in selected_features:
                continue
            if script not in self.unparsed.features[feat]:
                continue
            if lang not in self.unparsed.features[feat][script]:
                continue
            lookups += [(feat, self.unparsed.features[feat][script][lang])]

        # Sort the lookups by the order given in the LookupList table.
        res = []
        for feat, lk_idxs in sorted(lookups, key=lambda k: k[1]):
            for idx in lk_idxs:
                res.append((feat, self.unparsed.lookups[idx]))
        return res

    def _process_routine(self, tag, routine):
        if routine.name in self.processed_lookups:
            return
        self.processed_lookups.add(routine.name)

        for rule in routine.rules:
            if routine.name.startswith("SingleSubstitution"):
                self._process_simple_subs(tag, rule)
            elif routine.name.startswith("LigatureSubstitution"):
                self._process_simple_subs(tag, rule)
            elif routine.name.startswith("AlternateSubstitution"):
                self._process_alt_subs(tag, rule)
            elif routine.name.startswith("ChainedContextual"):
                self._process_chained_subs(tag, rule)
            else:
                print(f"Cannot process {rule.name}")

    def _memoize_input(self, input_, tag):
        res = {"input": "", "features": set([tag])}
        for glyph in input_:
            if glyph in self.glyph_inputs:
                res["features"] |= self.glyph_inputs[glyph]["features"]
                res["input"] += self.glyph_inputs[glyph]["input"]
        return res

    def _process_simple_subs(self, tag, rule):
        ## [["A"], ["B"], ["C", "D"]] --> [('A', 'B', 'C'), ('A', 'B', 'D')]
        inputs = list(itertools.product(*rule.input))
        for input_, result in zip(inputs, rule.replacement[0]):
            if result in self.glyph_inputs:
                continue
            self.glyph_inputs[result] = self._memoize_input(input_, tag)

    def _process_alt_subs(self, tag, rule):
        inputs = list(itertools.product(*rule.replacement))
        for input_, result in zip(inputs, rule.input[0]):
            if result in self.glyph_inputs:
                continue
            self.glyphs_input[result] = self._memoize_input(input_, tag)

    def _process_chained_subs(self, tag, rule):
        inputs = list(
                itertools.product(
                    *rule.precontext,
                    *rule.input,
                    *rule.postcontext
                )
        )
        # process lks
        for lookup_group in rule.lookups:
            if not lookup_group:
                continue
            for lk in lookup_group:
                self._process_routine(tag, lk.routine)

        for input_ in inputs:
            key = "-".join(input_)
            self.glyph_inputs[key] = self._memoize_input(input_, tag)


def main():
    # TODO (Marc F) Delete and use as module in bin scripts instead
    parser = ArgumentParser()
    parser.add_argument("font_before")
    args = parser.parse_args()

    font_before = TTFont(args.font_before)

    hb = FontGlyphs(font_before)
    hb.inputs(script="dev2", lang="dflt", features=["zero"])
    from pprint import pprint

    pprint(hb.glyph_inputs)
    print(len(hb.glyph_inputs))


if __name__ == "__main__":
    main()
