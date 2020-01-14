#!env python
import sys
from fontTools.ttLib import TTFont
from fontFeatures.tt2feaLib import unparse
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("input",
                    help="font file to process", metavar="FILE")
parser.add_argument("--gdef", dest="gdef", action='store_true',
                    help="Also output GDEF table information")
args = parser.parse_args()

font = TTFont(args.input)
ff = unparse(font, do_gdef = args.gdef)
print(ff.asFea())