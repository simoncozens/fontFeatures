from youseedee import ucd_data
from .BaseShaper import BaseShaper
import re
from fontFeatures.jankyPOS.Buffer import BufferItem
from .IndicShaperData import script_config, syllabic_category_map, syllabic_category_re, IndicPositionalCategory2IndicPosition, IndicPosition, reassign_category_and_position

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
        while len(category_string) > 0:
            state, end, matched_type = None, None, None
            for syllable_type in ["consonant_syllable", "vowel_syllable", "standalone_cluster","symbol_cluster","broken_cluster","other"]:
                m = re.match(syllabic_category_re[syllable_type], category_string)
                if m:
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

    def iterate_syllables(self):
        ix = 0
        while ix < len(self.buffer.items):
            syll_type = self.buffer.items[ix].syllable
            index = self.buffer.items[ix].syllable_index
            start = ix
            while ix < len(self.buffer.items) and self.buffer.items[ix].syllable_index == index:
                end = ix
                ix = ix + 1
            yield index, syll_type, start, end

    def initial_reordering(self, shaper):
        # Update consonant positions
        if self.config["base_pos"] == "last": # Not Sinhala
            for item in self.buffer.items:
                if item.indic_position == IndicPosition.BASE_C:
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
        if "rphf" in self.plan.fontfeatures.features and start + 3 > end \
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
                    for j in range(end-1,i,-1):
                        if is_consonant(j) or (disallow_double_halants and cat(j) == "H"):
                            break
                    if cat(j) != "H" and j > i:
                        self.buffer.items.insert(j, self.buffer.items.pop(i))
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
        for i in range(start, end+1):
            self.buffer.items[i].syllable_index = start - i

        # REORDER
        self.buffer.items[start:end+1] = sorted(self.buffer.items[start:end+1], key=lambda x:x.indic_position)

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

        for i in range(start, end+1):
            self.buffer.items[i].syllable_index = syllable_index

        # XXX set up masks
    def final_reordering(self, shaper):
        pass
