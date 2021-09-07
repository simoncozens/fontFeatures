from fontFeatures.shaperLib.SyllabicShaper import SyllabicShaper
from fontFeatures.ttLib import unparse
from babelfont import load
from fontFeatures.shaperLib.Buffer import Buffer
from fontFeatures.shaperLib.Shaper import Shaper
from fontFeatures.shaperLib.IndicShaper import IndicShaper
from fontFeatures.shaperLib.BaseShaper import BaseShaper
from fontTools.ttLib import TTFont
import unicodedata
from youseedee import ucd_data
from fontFeatures import RoutineReference


class BaseDeshaper(BaseShaper):
    def _run_stage(self, current_stage):
        print("kentucky")
        self.plan.msg("Running %s stage" % current_stage)
        self.plan.fontfeatures.hoist_languages()
        for stage in self.plan.stages:
            lookups = []
            if isinstance(stage, list):  # Features
                for f in stage:
                    if f not in self.plan.fontfeatures.features:
                        continue

                    routines = self.plan.fontfeatures.features[f]
                    routines = [x.routine if isinstance(x, RoutineReference) else x for x in routines]
                    lookups.extend(
                        [(routine, f) for routine in self._filter_by_lang(routines)]
                    )
                self.plan.msg("Processing features: %s" % ",".join(stage))
                for r, feature in lookups:
                    self.plan.msg(
                        "Before %s (%s)" % (r.name, feature), buffer=self.buffer
                    )
                    r.revert_buffer(self.buffer, stage=current_stage, feature=feature, namedclasses=self.plan.fontfeatures.namedClasses)
                    self.plan.msg(
                        "After %s (%s)" % (r.name, feature), buffer=self.buffer
                    )
            else:
                # It's a pause. We only support GSUB pauses.
                if current_stage == "sub":
                    stage(current_stage)

class SyllabicDeshaper(BaseDeshaper, SyllabicShaper):

    basic_features = ['cjct', 'vatu', 'pstf', 'half', 'abvf', 'blwf', 'pref', 'rkrf', 'rphf', 'akhn', 'nukt']
    after_syllable_features = ["locl", "ccmp"]
    other_features = ['clig', 'calt', 'haln', 'psts', 'blws', 'abvs', 'pres', 'init']
    repha = "Repha"

    def collect_features(self, shaper):
        shaper.add_pause(self.setup_syllables)
#        shaper.add_features(*self.other_features) <-- let's take care of these tomorrow
#        shaper.add_pause(self.final_reordering)
        for i in self.basic_features:
            shaper.add_features(i)
            shaper.add_pause()
#        shaper.add_pause(self.initial_reordering)
#        shaper.add_features(*self.after_syllable_features)


class IndicDeshaper(SyllabicDeshaper, IndicShaper):

    def override_features(self, shaper):
        shaper.disable_feature("liga")



class Deshaper(Shaper):
    INDIC_SHAPER = IndicDeshaper

    def collect_features(self, buf):
        """Determine the features, and their order, to process the buffer."""
        if hasattr(self.complexshaper, "override_features"):
            self.complexshaper.override_features(self)
        for uf in self.user_features:
            if not uf["value"]:  # Turn it off if it's already on
                self.disable_feature(uf["tag"])
            else:
                self.add_features(uf["tag"])
        if buf.direction == "LTR" or buf.direction == "RTL":
            self.add_features("rclt", "liga", "kern", "dist", "curs", "clig", "calt")
        else:
            self.add_features("vert")
        self.add_features("rlig", "mkmk", "mark", "locl", "ccmp", "blwm", "abvm")
        self.complexshaper.collect_features(self)
        self.add_features("rand", "dnom", "numr", "frac")
        if buf.direction == "LTR":
            self.add_features("ltrm", "ltra")
        elif buf.direction == "RTL":
            self.add_features("rtlm", "rtla")
        self.add_pause()
        self.add_features("rvrn")

    






font_path = "/Users/marcfoley/Type/fonts/ofl/poppins/Poppins-Black.ttf"
font = load(font_path)
ff = unparse(TTFont(font_path))

# Shape
buf = Buffer(font, unicodes="".join(["क़", " ", "क", "्", "क", "ि"]))
shaper = Shaper(ff, font)
shaper.execute(buf)
import pdb
pdb.set_trace()


# Deshape 
debuf = Buffer(font, unicodes="".join(["क़", " ", "क", "्", "क"]))
deshaper = Deshaper(ff, font)
deshaper.execute(debuf)

import pdb
pdb.set_trace()
print(debuf.items)