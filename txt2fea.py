#!env python
import sys
from fontFeatures.fontDameLib import unparse
from argparse import ArgumentParser
from fontFeatures.optimizer import Optimizer

parser = ArgumentParser()
parser.add_argument("--config",default=None,
                    help="config file to process", metavar="CONFIG")
parser.add_argument("input",
                    help="FontDame file to process", metavar="FILE")
parser.add_argument("--font",
                    help="font file to process", metavar="FONT")
parser.add_argument("--optimize", dest="optimize", action='store_true',
                    help="Run optimizer")

args = parser.parse_args()

parsed = unparse(args.input, args.config, font= args.font)
if args.optimize:
	Optimizer().optimize(parsed)

print(parsed.asFea())
