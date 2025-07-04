#!/usr/bin/env python
from fontFeatures.fontDameLib import unparse
from argparse import ArgumentParser

def main(args=None):
  parser = ArgumentParser()
  parser.add_argument("--config",default=None,
                      help="config file to process", metavar="CONFIG")
  parser.add_argument("input",
                      help="FontDame file to process", metavar="FILE")
  parser.add_argument("--font",
                      help="font file to process", metavar="FONT")
  parser.add_argument("--classfile",
                      help="class file to process", metavar="FEA")
  parser.add_argument("--optimize", dest="optimize", action='store_true',
                      help="Run optimizer")

  args = parser.parse_args(args)

  parsed = unparse(args.input, args.config, font= args.font)
  optlevel = 1
  if args.classfile:
    from fontTools.feaLib.parser import Parser
    parser = Parser(args.classfile)
    parser.parse()
    classes = parser.glyphclasses_.scopes_[0]
    parsed.scratch["glyphclasses"] = {}
    for k,v in classes.items():
      parsed.scratch["glyphclasses"][tuple(sorted(v.glyphs.glyphs))] = k
    parsed.scratch["index"] = 999

  # if args.optimize:
  # 	optlevel = 2
  # Optimizer(parsed).optimize(level=optlevel)

  print(parsed.asFea())

if __name__ == "__main__":
  main()