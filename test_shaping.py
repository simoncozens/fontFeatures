from fontFeatures.ttLib import unparse
from babelfont import load
from fontFeatures.shaperLib.Buffer import Buffer
from fontFeatures.shaperLib.Shaper import Shaper, Deshaper
from fontTools.ttLib import TTFont


font_path = "/Users/marcfoley/Type/fonts/ofl/tajawal/Tajawal-Regular.ttf"
font = load(font_path)
ff = unparse(TTFont(font_path))

# Shape
buf = Buffer(font, unicodes="".join(["الله"]))
shaper = Shaper(ff, font)
shaper.execute(buf) # -> uniFDF2
print(buf.serialize())

## Deshape 
debuf = Buffer(font, glyphs=["uniFDF2"], script="Arabic")
deshaper = Deshaper(ff, font)
deshaper.execute(debuf)
print(debuf.serialize())