from __future__ import print_function, division, absolute_import
from fontTools.feaLib.builder import addOpenTypeFeatures
from fontTools.ttLib import TTFont
import sys

from argparse import ArgumentParser, FileType

parser = ArgumentParser()
parser.add_argument("input",
                    help="font file to process", metavar="OTF")
parser.add_argument('feature', type=FileType('r'), default='-',nargs='?',
                    help="feature file(s) to add", metavar="FEA")
parser.add_argument("-o", dest="output",
                    help="path to output font", metavar="FILE")
args = parser.parse_args()
output = args.output
if output is None:
  output = "fea-"+args.input

font = TTFont(args.input)
print("Adding features")
addOpenTypeFeatures(font, args.feature)
print("Saving on "+output)
font.save(output)
