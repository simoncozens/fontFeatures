#!env python
import sys
from fontFeatures.fontDame2fee import unparse
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--config",default=None,
                    help="config file to process", metavar="CONFIG")
parser.add_argument("input",
                    help="font file to process", metavar="FILE")

args = parser.parse_args()

parsed = unparse(args.input, args.config)
from pprint import pprint
# pprint(parsed)
