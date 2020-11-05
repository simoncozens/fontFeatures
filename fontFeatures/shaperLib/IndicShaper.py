from youseedee import ucd_data
from .BaseShaper import BaseShaper
import re
from fontFeatures.shaperLib.Buffer import BufferItem
from .IndicShaperData import script_config, syllabic_category_map, syllabic_category_re, IndicPositionalCategory2IndicPosition, IndicPosition, reassign_category_and_position
import unicodedata

DOTTED_CIRCLE = 0x25CC

class IndicShaper(BaseShaper):

    basic_features = ['nukt', 'akhn', 'rphf', 'rkrf', 'pref', 'blwf', 'abvf', 'half', 'pstf', 'vatu', 'cjct']

    @property
    def config(self):
        return script_config.get(self.buffer.script, script_config["Invalid"])

    def collect_features(self, shaper):
        shaper.add_pause(self.setup_syllables)
        shaper.add_features("ccmp", "locl")
        shaper.add_pause(self.initial_reordering)
        for i in self.basic_features:
            shaper.add_features(i)
            shaper.add_pause()
        shaper.add_pause(self.final_reordering)
        shaper.add_features("init", "pres", "abvs", "blws", "psts", "haln")
        shaper.add_features("calt", "clig")

    def override_features(self, shaper):
        shaper.disable_feature("liga")


    def assign_indic_categories(self):
        serialized = []
        for ix,item in enumerate(self.buffer.items):
            ucd = ucd_data(item.codepoint)
            item.indic_syllabic_category = syllabic_category_map.get(ucd.get("Indic_Syllabic_Category", "Other"),"X")
            item.indic_positional_category = ucd.get("Indic_Positional_Category", "x")
            item.indic_position = IndicPositionalCategory2IndicPosition(item.indic_positional_category)
            reassign_category_and_position(item)
            serialized.append("<"+item.indic_syllabic_category+">("+item.indic_positional_category+")="+str(ix))
        return "".join(serialized)

    def setup_syllables(self, shaper):
        syllable_index = 0
        category_string = self.assign_indic_categories()
        self.plan.msg("Set up syllables: "+category_string)
        while len(category_string) > 0:
            state, end, matched_type = None, None, None
            for syllable_type in ["consonant_syllable", "vowel_syllable", "standalone_cluster","symbol_cluster","broken_cluster","other"]:
                m = re.match(syllabic_category_re[syllable_type], category_string)
                if m and len(m[0]):
                    matched_type = syllable_type
                    category_string = category_string[len(m[0]):]
                    indexes = re.findall("=(\\d+)", m[0])
                    start, end = int(indexes[0]), int(indexes[-1])
                    break
            assert(matched_type)
            for i in range(start, end+1):
                self.buffer.items[i].syllable_index = syllable_index
                self.buffer.items[i].syllable = syllable_type
            syllable_index = syllable_index+1
        self.plan.msg("Syllables", self.buffer, ["syllable_index", "syllable"])

    def iterate_syllables(self):
        ix = 0
        while ix < len(self.buffer.items):
            syll_type = self.buffer.items[ix].syllable
            index = self.buffer.items[ix].syllable_index
            start = ix
            while ix < len(self.buffer.items) and self.buffer.items[ix].syllable_index == index:
                ix = ix + 1
                end = ix
            yield index, syll_type, start, end

    def consonant_position_from_face(self, consonant):
        virama = self.config["virama"]
        consonant_item = BufferItem.new_unicode(consonant)
        virama_item = BufferItem.new_unicode(virama)
        consonant_item.map_to_glyph(self.buffer.font)
        virama_item.map_to_glyph(self.buffer.font)

        if self.would_substitute("blwf", [virama_item, consonant_item]):
            return IndicPosition.BELOW_C
        if self.would_substitute("blwf", [consonant_item, virama_item]):
            return IndicPosition.BELOW_C
        if self.would_substitute("vatu", [virama_item, consonant_item]):
            return IndicPosition.BELOW_C
        if self.would_substitute("vatu", [consonant_item, virama_item]):
            return IndicPosition.BELOW_C

        if self.would_substitute("pstf", [virama_item, consonant_item]):
            return IndicPosition.POST_C
        if self.would_substitute("pstf", [consonant_item, virama_item]):
            return IndicPosition.POST_C

        if self.would_substitute("pref", [virama_item, consonant_item]):
            return IndicPosition.POST_C
        if self.would_substitute("pref", [consonant_item, virama_item]):
            return IndicPosition.POST_C
        return IndicPosition.BASE_C

    def initial_reordering(self, shaper):
        # Update consonant positions
        if self.config["base_pos"] == "last": # Not Sinhala
            for item in self.buffer.items:
                if item.indic_position == IndicPosition.BASE_C:
                    item.indic_position = self.consonant_position_from_face(item.codepoint)
                    # XXX Consonant position from face
                    pass
        # Insert dotted circles
        for ix,i in enumerate(self.buffer.items):
            if i.syllable == "broken_cluster" and (ix == 0 or i.syllable_index != self.buffer.items[ix-1].syllable_index):
                # Need to insert dotted circle.
                dotted_circle = BufferItem.new_unicode(DOTTED_CIRCLE)
                dotted_circle.syllable_index = i.syllable_index
                dotted_circle.syllable = i.syllable
                dotted_circle.indic_syllabic_category = "DOTTEDCIRCLE"
                dotted_circle.indic_position = IndicPosition.END
                dotted_circle.map_to_glyph(self.buffer.font)
                if i.indic_syllabic_category == "Repha":
                    self.buffer.items.insert(ix+1, dotted_circle)
                else:
                    self.buffer.items.insert(ix, dotted_circle)
        # Syllable-specific
        for index,syll_type,start,end in self.iterate_syllables():
            if syll_type in ["vowel_syllable", "consonant_syllable"]:
                self.initial_reordering_consonant_syllable(start,end)
            elif syll_type in ["broken_cluster", "standalone_cluster"]:
                self.initial_reordering_standalone_cluster(start,end)

    def initial_reordering_standalone_cluster(self, start, end):
        # We could emulate a Uniscribe bug here, but we won't.
        return self.initial_reordering_consonant_syllable(start, end)

    def initial_reordering_consonant_syllable(self, start, end):
        def cat(i):
            return self.buffer.items[i].indic_syllabic_category
        def pos(i):
            return self.buffer.items[i].indic_position
        def swap(a,b):
            self.buffer.items[b], self.buffer.items[a] = self.buffer.items[a], self.buffer.items[b]
        def is_joiner(n):
            return cat(n) == "ZWJ" or cat(n) == "ZWNJ"
        def is_consonant(n):
            isc = cat(n)
            is_medial = isc == "CM"
            return isc in ["C", "CS", "Ra", "V", "PLACEHOLDER", "DOTTEDCIRCLE"] or is_medial

        if self.buffer.script == "Kannada" and start + 3 <= end and cat(start) == "Ra" and cat(start+1) == "H" and cat(start+2) == "ZWJ":
            swap(start+1, start+2)

        syllable_index = self.buffer.items[start].syllable_index

        base = end
        has_reph = False

        limit = start
        if "rphf" in self.plan.fontfeatures.features and start + 3 <= end \
            and ( \
                (self.config["reph_mode"] == "implicit" and not is_joiner(start+2)) \
                or (self.config["reph_mode"] == "explicit" and cat(start+2) == "ZWJ") \
            ):
            if self.would_substitute("rphf", self.buffer.items[start:start+2]) \
                or self.would_substitute("rphf", self.buffer.items[start:start+3]):
                limit = limit + 2
            while limit < end and is_joiner(limit):
                limit = limit + 1
            base = start
            has_reph = True
        elif self.config["reph_mode"] == "log_repha" and cat(start) == "Repha":
            limit = limit + 1
            while limit < end and is_joiner(limit):
                limit = limit + 1
            base = start
            has_reph = True

        if self.config["base_pos"] == "last":
            i = end
            seen_below = False
            while True:
                i = i -1
                if is_consonant(i):
                    if pos(i) != IndicPosition.BELOW_C and \
                        (pos(i) != IndicPosition.POST_C or seen_below):
                        base = i
                        break
                    if pos(i) == IndicPosition.BELOW_C:
                        seen_below = True
                    base = i
                else:
                    if start < i and cat(i) == "ZWJ" and cat(i-1) == "H":
                        break
                if i <= limit:
                    break
        elif self.config["base_pos"] == "last_sinhala":
            if not has_reph:
                base = limit
            for i in range(limit, end):
                if is_consonant(i):
                    if limit < i and cat(i-1) == "ZWJ":
                        break
                    else:
                        base = i
            for i in range(base+1, end):
                if is_consonant(i):
                    self.buffer.items[i].indic_position = IndicPosition.BELOW_C

        if has_reph and base == start and limit - base <= 2:
            has_reph = False

        self.plan.msg("Base consonant for syllable %i is %s" % (syllable_index, self.buffer[base].glyph))
        for i in range(start, base):
            self.buffer.items[i].indic_position = min(IndicPosition.PRE_C, pos(i))
        if base < end:
            self.buffer.items[i].indic_position = IndicPosition.BASE_C

        # Mark final consonants
        for i in range(base+1, end):
            if cat(i) == "M":
                for j in range(i, end):
                    if is_consonant(j):
                        self.buffer.items[j].indic_position = IndicPosition.FINAL_C
                        break
                break

        if has_reph:
            self.buffer.items[start].indic_syllabic_category = IndicPosition.RA_TO_BECOME_REPH

        if self.config["old_spec"]:
            disallow_double_halants = self.buffer.script == "Kannada"
            for i in range(base+1, end):
                if cat(i) == "H":
                    j = end - 1
                    while j > i:
                        if is_consonant(j) or (disallow_double_halants and cat(j) == "H"):
                            break
                        j = j - 1
                    if cat(j) != "H" and j > i:
                        self.buffer.items.insert(j, self.buffer.items.pop(i))
                        self.plan.msg("Moved double halant", self.buffer)
                    break

        last_pos = IndicPosition.START
        for i in range(start, end):
            if cat(i) in ["ZWJ", "ZWNJ", "N", "RS", "CM", "H"]:
                self.buffer.items[i].indic_position = last_pos
                if cat(i) == "H" and pos(i) == IndicPosition.PRE_M:
                    for j in range(i,start,-1):
                        if pos(j-1) != IndicPosition.PRE_M:
                            self.buffer.items[i].indic_position = pos(j-1)
                            break
            elif pos(i) != IndicPosition.SMVD:
                last_pos = pos(i)

        last = base
        for i in range(base+1, end):
            if is_consonant(i):
                for j in range(last+1, i):
                    if pos(j) < IndicPosition.SMVD:
                        self.buffer.items[j].indic_position = pos(i)
                last = i
            elif cat(i) == "M":
                last = i

        # As with Harfbuzz, temporarily abuse syllable index
        for i in range(start, end):
            self.buffer.items[i].syllable_index = start - i

        # REORDER
        self.buffer.items[start:end] = sorted(self.buffer.items[start:end], key=lambda x:x.indic_position)

        base = end
        for i in range(start, end):
            if pos(i) == IndicPosition.BASE_C:
                base = i
                break

        if self.config["old_spec"] or end - start > 127:
            # Merge clusters
            pass
        else:
            for i in range(base, end):
                if self.buffer.items[i].syllable_index != 255:
                    max_i = i
                    j = start + self.buffer.items[i].syllable_index
                    while j != i:
                        max_i = max(max_i, j)
                        next_i = start + self.buffer.items[j].syllable_index
                        self.buffer.items[j].syllable_index = 255
                        j = next_i
                    if i != max_i:
                        # Merge clusters
                        pass

        for i in range(start, end):
            self.buffer.items[i].syllable_index = syllable_index
        self.plan.msg("After initial reordering", self.buffer)

        # Set up masks now. Note that these masks have the opposite
        # value to Harfbuzz - i.e. False means "not masked"
        rphf_mask = False
        for i in range(start, end):
            if pos(i) != IndicPosition.RA_TO_BECOME_REPH:
                rphf_mask = True
            self.buffer.items[i].feature_masks["rphf"] = rphf_mask
            self.buffer.items[i].feature_masks["half"] = i > base
            if not self.config["old_spec"] and self.config["blwf_mode"] == "pre_and_post":
                self.buffer.items[i].feature_masks["blwf"] = i > base
            self.buffer.items[i].feature_masks["blwf"] = i < base
            self.buffer.items[i].feature_masks["abvf"] = i < base
            self.buffer.items[i].feature_masks["pstf"] = i < base

        # We are not supporting old spec eyelash ra

        # pref substitutes pairwise
        pref_len = 2
        i = base + 1
        for j in range(0,i):
            self.buffer.items[j].feature_masks["pref"] = True
        while i < end-pref_len:
            if self.would_substitute("pref", [self.buffer.items[i], self.buffer.items[i+1]]):
                self.buffer.items[i].feature_masks["pref"] = False
                self.buffer.items[i+1].feature_masks["pref"] = False
                i = i + 2
            else:
                self.buffer.items[i].feature_masks["pref"] = True
                i = i + 1

        # ZWJ/ZWNJ
        for i in range(start+1, end):
            if cat(i) in ["ZWJ", "ZWNJ"]:
                non_joiner == cat(i) == "ZWNJ"
                j = i
                while True:
                    j = j - 1
                    if non_joiner:
                        self.buffer.items[j].feature_masks["half"] = True
                    if not (j > start and not is_consonant(j)):
                        break

    def final_reordering(self, shaper):
        for index,syll_type,start,end in self.iterate_syllables():
            self.final_reordering_syllable(start,end)

    def final_reordering_syllable(self, start, end):
        def cat(i):
            return self.buffer.items[i].indic_syllabic_category
        def pos(i):
            return self.buffer.items[i].indic_position
        def swap(a,b):
            self.buffer.items[b], self.buffer.items[a] = self.buffer.items[a], self.buffer.items[b]
        def is_joiner(n):
            return cat(n) == "ZWJ" or cat(n) == "ZWNJ"
        def is_halant(n):
            return cat(n) == "H"
        def is_consonant(n):
            isc = cat(n)
            is_medial = isc == "CM"
            return isc in ["C", "CS", "Ra", "V", "PLACEHOLDER", "DOTTEDCIRCLE"] or is_medial

        virama = self.config["virama"]
        virama_item = BufferItem.new_unicode(virama)
        virama_item.map_to_glyph(self.buffer.font)
        if virama_item.glyph != ".notdef":
            for i in range(start, end):
                if self.buffer.items[i].glyph == virama_item.glyph \
                    and self.buffer.items[i].ligated \
                    and self.buffer.items[i].multiplied:
                    self.buffer.items[i].indic_syllabic_category = "H"
                    self.buffer.items[i].ligated = False
                    self.buffer.items[i].multiplied = False
        try_pref = any(["pref" in item.feature_masks and item.feature_masks["pref"] == False for item in self.buffer.items])
        base = start
        while base < end:
            if pos(base) >= IndicPosition.BASE_C:
                if try_pref and base + 1 < end:
                    for i in range(base+1, end):
                        item = self.buffer.items[i]
                        if not item.feature_masks.get("pref",True):
                            if not (item.substituted and (item.ligated and not item.multiplied)):
                                base = i
                                while base < end and is_halant(base):
                                    base = base + 1
                                self.buffer.items[base].indic_positional_category = IndicPosition.BASE_C
                                try_pref = false
                            break
                if self.buffer.script == "Malayalam":
                    i = base + 1
                    while i < end:
                        while i < end and is_joiner(i):
                            i = i + 1
                        if i == end or not is_halant(i):
                            break
                        i = i + 1
                        while i < end and is_joiner(i):
                            i = i + 1
                        if i < end and is_consonant(i) and pos(i) == IndicPosition.BELOW_C:
                            base = i
                            self.buffer.items[base].indic_positional_category = IndicPosition.BASE_C
                        i = i + 1
                if start < base and pos(base) > IndicPosition.BASE_C:
                    base = base - 1
                break
            base = base + 1
        if base == end and start < base and cat(base-i) == "ZWJ":
            base = base - 1
        if base < end:
            while start < base and cat(base) in ["N","H"]:
                base = base - 1

        # Reorder matras
        if start + 1 < end and start < base:
            new_pos = base -1
            if base == end:
                new_pos = base - 2
            # XXX

        for i in range(start,end):
            self.buffer.items[i].feature_masks["init"] = True
        if pos(start) == IndicPosition.PRE_M:
            if start == 0 or ucd_data(self.buffer.font.codepointForGlyph(self.buffer.items[start-1].glyph))["General_Category"] not in ["Cf", "Cn", "Co", "Cs", "Ll", "Lm", "Lo", "Lt", "Lu", "Mc", "Me", "Mn"]:
                self.buffer.items[start].feature_masks["init"] = False


    def normalize_unicode_buffer(self):
        unicodes = [item.codepoint for item in self.buffer.items]
        newunicodes = []
        for cp in unicodes:
            if cp in [0x0931, 0x09DC, 0x09DD, 0x0B94]:
                newunicodes.append(cp)
            elif cp in [0x0DDA, 0x0DDC, 0x0DDD, 0x0DDE]: # Sinhala split matras
                glyph = BufferItem.new_unicode(cp)
                glyph.map_to_glyph(self.buffer.font)
                if self.would_substitute("pstf", [glyph]):
                    newunicodes.append(0x0DD9, cp)
                else:
                    newunicodes.append(cp)
            else:
                newunicodes.extend([ord(x) for x in unicodedata.normalize("NFD", chr(cp)) ])
        # Now recompose
        newstring = ""
        ix = 0
        while ix < len(newunicodes):
            a = newunicodes[ix]
            if ix+1 == len(newunicodes):
                newstring = newstring + chr(a)
                break

            b = newunicodes[ix+1]
            s = chr(a) + chr(b)
            composed = unicodedata.normalize("NFC", s)
            if ucd_data(a)["General_Category"][0] == "M":
                newstring = newstring + chr(a)
                ix = ix + 1
                continue
            elif a == 0x9af and b == 0x9bc:
                newstring = newstring + chr(0x9df)
                ix = ix + 2
                continue
            elif composed != unicodedata.normalize("NFD", s):
                assert(len(s) == 1)
                newunicodes[ix] = ord(x)
                del newunicodes[ix+1]
                continue
            else:
                newstring = newstring + chr(a)
                ix =ix + 1

        self.buffer.store_unicode(newstring)

