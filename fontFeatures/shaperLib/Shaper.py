from fontFeatures.fontProxy import FontProxy
from fontFeatures import FontFeatures
import unicodedata
from fontFeatures.jankyPOS import Buffer
from .BaseShaper import BaseShaper
from .ArabicShaper import ArabicShaper
from youseedee import ucd_data


class Shaper:
    def __init__(self, ff, font):
        assert isinstance(ff, FontFeatures)
        assert isinstance(font, FontProxy)
        self.fontfeatures = ff
        self.fontproxy = font

    def execute(self, buf, features=[]):
        # Choose complex shaper
        self.complexshaper = self.categorize(buf)(self, self.fontproxy, buf, features)
        self.stages = [[]]
        if isinstance(features, str):
            self.user_features = self.parse_user_feature_string(features)
        else:
            self.user_features = features
        self.collect_features(buf)
        self.complexshaper.shape()
        return buf

    def parse_user_feature_string(self, features):
        features = features.split(",")
        outfeat = []
        for f in features:
            f = f.rstrip()
            m = re.match("^([+\-]?)(\w+)", f)
            if m:
                outfeat.append({"tag": m[2], "value": m[1] == "+"})
                continue
            m = re.match("^(\w+)=([10])", f)
            if m:
                outfeat.append({"tag": m[1], "value": m[2] == "1"})
            else:
                outfeat.append({"tag": f, "value": True})
        return outfeat

    def add_pause(self, thing = None):
        if thing:
            self.stages.append(thing)
        self.stages.append([])

    def add_features(self, *tags):
        for t in tags:
            if any([isinstance(x, list) and t in x for x in self.stages]):
                continue
            self.stages[-1].append(t)

    def disable_feature(self, tag):
        for s in self.stages:
            if tag in s:
                s.remove(tag)

    def collect_features(self, buf):
        self.add_features("rvrn")
        self.add_pause()
        if buf.direction == "LTR":
            self.add_features("ltra", "ltrm")
        elif buf.direction == "RTL":
            self.add_features("rtla", "rtlm")
        self.add_features("frac", "numr", "dnom", "rand")
        # trak?
        self.complexshaper.collect_features(self)
        # common features
        self.add_features("abvm", "blwm", "ccmp", "locl", "mark", "mkmk", "rlig")
        if buf.direction == "LTR" or buf.direction == "RTL":
            self.add_features("calt", "clig", "curs", "dist", "kern", "liga", "rclt")
        else:
            self.add_features("vert")
        for uf in self.user_features:
            if not uf["value"]:  # Turn it off if it's already on
                self.disable_feature(uf["tag"])
            else:
                self.add_features(uf["tag"])
        if hasattr(self.complexshaper, "override_features"):
            self.complexshaper.override_features(self)

    def categorize(self, buf):
        if buf.script == "Arabic":
            return ArabicShaper

        if buf.script in [
            "Mongolian",
            "Syriac",
            "Nko",
            "Phags_Pa",
            "Mandaic",
            "Manichaean",
            "Psalter_Pahlavi",
            "Adlam",
            "Hanifi_Rohingya",
            "Sogdian",
        ]:
            if buf.script == self.font.supported_script(buf.script).lower():
                return ArabicShaper
            else:
                return BaseShaper

        if buf.script in ["Thai", "Lao"]:
            return ThaiShaper
        if buf.script == "Hangul":
            return HangulShaper
        if buf.script == "Hebrew":
            return HebrewShaper
        if buf.script in [
            "Bengali",
            "Devanagari",
            "Gujarati",
            "Gurmukhi",
            "Kannada",
            "Malayalam",
            "Oriya",
            "Tamil",
            "Telugu",
            "Sinhala",
        ]:
            if self.font.supported_script(buf.script).endswith("3"):
                return USEShaper
            else:
                return IndicShaper
        if buf.script == "Khmer":
            return KhmerShaper

        if buf.script == "Mymanmar":
            if self.font.supported_script(buf.script) == "mymr":
                return BaseShaper
            else:
                return MyanmarShaper

        # if buf.script = "Qaag": return MyanmarZawgyiShaper
        if buf.script in [
            "Tibt",
            "Buhd",
            "Hano",
            "Tglg",
            "Tagb",
            "Limb",
            "Tale",
            "Bugi",
            "Khar",
            "Sylo",
            "Tfng",
            "Bali",
            "Cham",
            "Kali",
            "Lepc",
            "Rjng",
            "Saur",
            "Sund",
            "Egyp",
            "Java",
            "Kthi",
            "Mtei",
            "Lana",
            "Tavt",
            "Batk",
            "Brah",
            "Cakm",
            "Shrd",
            "Takr",
            "Dupl",
            "Gran",
            "Khoj",
            "Sind",
            "Mahj",
            "Modi",
            "Hmng",
            "Sidd",
            "Tirh",
            "Ahom",
            "Bhks",
            "Marc",
            "Newa",
            "Gonm",
            "Soyo",
            "Zanb",
            "Dogr",
            "Gong",
            "Maka",
            "Nand",
        ]:
            return USEShaper
        return BaseShaper

def _script_direction(script):
    if script in [
        "Arabic",
        "Hebrew",
        "Syriac",
        "Thaana",
        "Cypriot",
        "Kharoshthi",
        "Phoenician",
        "Nko",
        "Lydian",
        "Avestan",
        "Imperial_Aramaic",
        "Inscriptional_Parthian",
        "Inscriptional_Pahlavi",
        "Old_South_Arabian",
        "Old_Turkic",
        "Samaritan",
        "Mandaic",
        "Meroitic_Cursive",
        "Meroitic_Hieroglyphs",
        "Manichaean",
        "Mende_Kikakui",
        "Nabataean",
        "Old_North_Arabian",
        "Palmyrene",
        "Psalter_Pahlavi",
        "Hatran",
        "Adlam",
        "Hanifi_Rohingya",
        "Old_Sogdian",
        "Sogdian",
        "Elymaic",
        "Chorasmian",
        "Yezidi"]:
        return "RTL"
    if script in ["Old_Hungarian", "Old_Italic", "Runic"]:
        return "invalid"
    return "LTR"
