#!env python
import sys
from fontTools.ttLib import TTFont
from fontFeatures.ttLib import unparse
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("input",
                    help="font file to process", metavar="FILE")
parser.add_argument("--gdef", dest="gdef", action='store_true',
                    help="Also output GDEF table information")
parser.add_argument("--no-lookups", dest="nolookups", action='store_true',
                    help="Just list languages and features, don't unparse lookups")
parser.add_argument("--config",default=None,
                    help="config file to process", metavar="CONFIG")

args = parser.parse_args()

config = {}
if args.config:
  import json
  with open(args.config) as f:
      config = json.load(f)

font = TTFont(args.input)
ff = unparse(font, do_gdef = args.gdef, doLookups = (not args.nolookups), config = config)
print(ff.asFea())