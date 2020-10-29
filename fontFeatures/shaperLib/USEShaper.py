from youseedee import ucd_data
from .ArabicShaper import ArabicShaper
import re
from fontFeatures.shaperLib.Buffer import BufferItem
import unicodedata

DOTTED_CIRCLE = 0x25CC

class USEShaper(ArabicShaper):
    # Inheriting from Arabic shaper gets us joining information for free

    basic_features = ['rkrf', 'abvf', 'blwf', 'half', 'pstf', 'vatu', 'cjct' ]
    topographical_features = ['isol', 'init', 'medi', 'fina' ]
    other_features = ['abvs', 'blws', 'haln', 'pres', 'psts' ]

    def collect_features(self, shaper):
        shaper.add_pause(self.setup_syllables)
        # Default glyph pre-processing
        shaper.add_features("locl", 'ccmp', 'nukt', 'akhn')
        shaper.add_pause(self.clear_substitution)
        shaper.add_features('rphf')
        shaper.add_pause(self.record_rphf_use)
        shaper.add_pause(self.clear_substitution)
        shaper.add_features('pref')
        shaper.add_pause(self.record_pref_use)

        shaper.add_features(*self.basic_features)
        shaper.add_pause(self.reorder_use)
        shaper.add_pause(self.clear_syllables)
        shaper.add_features(*self.topographical_features)
        shaper.add_pause()
        shaper.add_features(*self.other_features)

    def substitute_default(self):
        super().substitute_default()
        # Grab USE info here
        for item in self.buffer.items:
            item.use_category = ucd_data(item.codepoint).get("USE_Category", "")

    def cat(self,i):
        return self.buffer.items[i].use_category

    def setup_syllables(self):
        self.find_syllables()
        self.setup_rphf_mask()
        self.setup_topographical_masks()

    def setup_rphf_mask(self):
        for index,syll_type,start,end in self.iterate_syllables():
            if self.cat(start) == "R":
                limit = 1
            else:
                limit = min(3, end-start)
            for i in range(start,end):
                self.buffer.items[i].feature_masks["rphf"] = i > start+limit
