#!env python
import sys
from fontFeatures.feaLib import FeaUnparser
from fontFeatures.optimizer import Optimizer
from argparse import ArgumentParser

import logging
import os

LOGLEVEL = os.environ.get("LOGLEVEL", "WARNING").upper()
logging.basicConfig(level=LOGLEVEL)

import warnings


def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    return "# [warning] %s\n" % (message)


warnings.formatwarning = warning_on_one_line

parser = ArgumentParser()
parser.add_argument("input", help="feature file to process", metavar="FILE")
parser.add_argument(
    "--optimize", dest="optimize", action="store_true", help="Run optimizer"
)

args = parser.parse_args()
ff = FeaUnparser(open(args.input, "r")).ff
if args.optimize:
    Optimizer().optimize(ff)
print(ff.asFea())
