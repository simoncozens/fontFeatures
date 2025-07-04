#!/usr/bin/env python3
from fontFeatures.shaperLib.Buffer import Buffer
from fontFeatures.ttLib import unparse
from fontTools.ttLib import TTFont
from fontFeatures.shaperLib.Shaper import Shaper
import sys
from babelfont import load
from fontTools.ttLib import TTFont
import argparse
import logging
import re

def main(args=None):
    parser = argparse.ArgumentParser(description='Shape text')
    parser.add_argument('font', metavar='OTF',
                        help='Font file')
    parser.add_argument('--verbose', '-V', action="count", dest='logging',
                        help='Output interim shaping results')
    parser.add_argument("--ned", "--no-extra-data", dest="ned", action='store_true', help="No Extra Data; Do not output clusters or advances")
    parser.add_argument("--no-glyph-names", dest="ngn", action='store_true', help="Output glyph indices instead of names")
    parser.add_argument("--no-positions", dest="np", action='store_true', help="Do not output glyph positions")
    parser.add_argument("--additional", help='Additional information')
    parser.add_argument('--features', help='Feature string')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-u', help='Unicodes')
    group.add_argument('string', metavar='STRING',
                        help='Text to shape', nargs="?")

    args = parser.parse_args(args)

    logging.basicConfig(format='%(message)s')

    if args.logging:
        logging.getLogger("fontFeatures.shaperLib").setLevel(logging.INFO)
        if args.logging >= 2:
            logging.getLogger("fontFeatures.shaperLib").setLevel(logging.DEBUG)

    font = load(args.font)
    if args.font.endswith(".ttf") or args.font.endswith(".otf"):
        ff = unparse(TTFont(args.font))
    if args.u:
        args.u = re.sub("[uU]+|0x", "", args.u)
        splitup = re.split(r"[\s,]", args.u)
        args.string = "".join([chr(int(x,16)) for x in splitup])

    buf = Buffer(font, unicodes=args.string)
    shaper = Shaper(ff, font)
    if args.features:
        shaper.execute(buf, features=args.features)
    else:
        shaper.execute(buf)
    serialize_options = {}
    if args.ngn:
        serialize_options["names"] = False
    if args.ned:
        serialize_options["ned"] = True
    if args.np:
        serialize_options["position"] = False
    if args.additional:
        serialize_options["additional"] = args.additional
    if buf.direction == "RTL":
        buf.items = list(reversed(buf.items))
    print(buf.serialize(**serialize_options))

if __name__ == "__main__":
    main()