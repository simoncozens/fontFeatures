from .BaseShaper import BaseShaper
from youseedee import ucd_data


jts = {
	"U": 0, "L": 1, "R": 2, "D": 3, "ALAPH": 4, "DALATH_RISH": 5
}
state_table = [
  #   jt_U,          jt_L,          jt_R,          jt_D,          jg_ALAPH,      jg_DALATH_RISH */

  # State 0: prev was U, not willing to join.
  [ ("NONE","NONE",0), ("NONE","ISOL",2), ("NONE","ISOL",1), ("NONE","ISOL",2), ("NONE","ISOL",1), ("NONE","ISOL",6), ],

  # State 1: prev was R or ISOL/ALAPH, not willing to join.
  [ ("NONE","NONE",0), ("NONE","ISOL",2), ("NONE","ISOL",1), ("NONE","ISOL",2), ("NONE","FIN2",5), ("NONE","ISOL",6), ],

  # State 2: prev was D/L in ISOL form, willing to join.
  [ ("NONE","NONE",0), ("NONE","ISOL",2), ("INIT","FINA",1), ("INIT","FINA",3), ("INIT","FINA",4), ("INIT","FINA",6), ],

  # State 3: prev was D in FINA form, willing to join.
  [ ("NONE","NONE",0), ("NONE","ISOL",2), ("MEDI","FINA",1), ("MEDI","FINA",3), ("MEDI","FINA",4), ("MEDI","FINA",6), ],

  # State 4: prev was FINA ALAPH, not willing to join.
  [ ("NONE","NONE",0), ("NONE","ISOL",2), ("MED2","ISOL",1), ("MED2","ISOL",2), ("MED2","FIN2",5), ("MED2","ISOL",6), ],

  # State 5: prev was FIN2/FIN3 ALAPH, not willing to join.
  [ ("NONE","NONE",0), ("NONE","ISOL",2), ("ISOL","ISOL",1), ("ISOL","ISOL",2), ("ISOL","FIN2",5), ("ISOL","ISOL",6), ],

  # State 6: prev was DALATH/RISH, not willing to join.
  [ ("NONE","NONE",0), ("NONE","ISOL",2), ("NONE","ISOL",1), ("NONE","ISOL",2), ("NONE","FIN3",5), ("NONE","ISOL",6),],
]


class ArabicShaper(BaseShaper):
    def substitute_default(self):
        state = 0
        prev = ~1
        self.buffer.arabic_joining = ["NONE" for x in range(len(self.buffer.unicodes))]
        for ix,g in enumerate(self.buffer.unicodes):
            ucd = ucd_data(g)
            joining = ucd.get("Joining_Type","U")
            if joining == "T": continue
            if ucd.get("Joining_Group") == "ALAPH": joining = "ALAPH"
            if ucd.get("Joining_Group") == "DALATH RISH": joining = "DALATH_RISH"
            prev, this, state = state_table[state][jts[joining]]
            if ix > 0:
            	self.buffer.arabic_joining[ix-1] = prev
            self.buffer.arabic_joining[ix] = this
        import code; code.interact(local=locals())
