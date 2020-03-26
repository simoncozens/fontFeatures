from fontTools.ttLib import TTFont

class FontFeatures:
  def __init__(self):
    self.namedClasses = {}
    self.routines = []
    self.features = {}

class Routine:
	def __init__(self, name, rules = [], address = None):
		self.name  = name
		self.rules = rules
		self.address = address

class Substitution:

	def __init__(self, input_, replacement, precontext = [], postcontext = [], address = None):
		self.precontext = precontext
		self.postcontext = postcontext
		self.input = input_
		self.replacement = replacement
		self.address = address