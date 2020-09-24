from .BaseShaper import BaseShaper
from youseedee import ucd_data


jts = {
  "U": 0, "L": 1, "R": 2, "D": 3, "ALAPH": 4, "DALATH_RISH": 5
}
state_table = [
  #   jt_U,          jt_L,          jt_R,          jt_D,          jg_ALAPH,      jg_DALATH_RISH */

  # State 0: prev was U, not willing to join.
  [ ("none","none",0), ("none","isol",2), ("none","isol",1), ("none","isol",2), ("none","isol",1), ("none","isol",6), ],

  # State 1: prev was R or ISOL/ALAPH, not willing to join.
  [ ("none","none",0), ("none","isol",2), ("none","isol",1), ("none","isol",2), ("none","fin2",5), ("none","isol",6), ],

  # State 2: prev was D/L in ISOL form, willing to join.
  [ ("none","none",0), ("none","isol",2), ("init","fina",1), ("init","fina",3), ("init","fina",4), ("init","fina",6), ],

  # State 3: prev was D in FINA form, willing to join.
  [ ("none","none",0), ("none","isol",2), ("medi","fina",1), ("medi","fina",3), ("medi","fina",4), ("medi","fina",6), ],

  # State 4: prev was FINA ALAPH, not willing to join.
  [ ("none","none",0), ("none","isol",2), ("med2","isol",1), ("med2","isol",2), ("med2","fin2",5), ("med2","isol",6), ],

  # State 5: prev was FIN2/FIN3 ALAPH, not willing to join.
  [ ("none","none",0), ("none","isol",2), ("isol","isol",1), ("isol","isol",2), ("isol","fin2",5), ("isol","isol",6), ],

  # State 6: prev was DALATH/RISH, not willing to join.
  [ ("none","none",0), ("none","isol",2), ("none","isol",1), ("none","isol",2), ("none","fin3",5), ("none","isol",6),],
]


class ArabicShaper(BaseShaper):
    def collect_features(self, shaper):
        # shaper.add_features("stch")
        shaper.add_features("ccmp", "locl")
        shaper.add_pause(self.do_arabic_joining)
        shaper.add_features("rlig", "rclt", "calt")
        shaper.add_pause()
        shaper.add_features("mset")

    def substitute_default(self):
        super().substitute_default()
        state = 0
        prev_item = None
        for item in self.buffer.items:
            item.arabic_joining = "NONE"
            ucd = ucd_data(item.codepoint)
            joining = ucd.get("Joining_Type","U")
            if joining == "T": continue
            if ucd.get("Joining_Group") == "ALAPH": joining = "ALAPH"
            if ucd.get("Joining_Group") == "DALATH RISH": joining = "DALATH_RISH"
            prev, this, state = state_table[state][jts[joining]]
            if prev_item:
              prev_item.arabic_joining = prev
            item.arabic_joining = this
            prev_item = item

    def do_arabic_joining(self, current_stage):
        if current_stage != "sub":
            return

        for f in ['isol', 'fina', 'fin2', 'fin3', 'medi', 'med2', 'init']:
            if f not in self.plan.fontfeatures.features:
                continue
            for routine in self.plan.fontfeatures.features[f]:
                self.buffer.set_mask(routine.flags, routine.markFilteringSet)
                # Additional mask
                self.buffer.mask = list(filter(lambda ix: self.buffer.items[ix].arabic_joining == f, self.buffer.mask))
                for r in routine.rules:
                    if r.stage != "sub":
                        continue
                    if r.apply_to_buffer(self.buffer):
                        break

