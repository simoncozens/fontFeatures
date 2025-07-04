#!/bin/env python3
"""Stupid Inefficient Exhaustive Shaping Test Architecture."""
import argparse
import json
import os
import random
import sys
import itertools
import re

import fontFeatures
import tqdm
from babelfont import load
from fontFeatures.shaperLib.Buffer import Buffer
from fontFeatures.shaperLib.Shaper import Shaper
from fontFeatures.ttLib import unparse
from fontTools.ttLib import TTFont
from vharfbuzz import Vharfbuzz

def main(args=None):
    parser = argparse.ArgumentParser(description="Test coverage of OT features.")
    subparsers = parser.add_subparsers(required=True, dest="cmd")
    report = subparsers.add_parser("report")
    report.add_argument("--suite", help="Test suite to read", metavar="JSON", required=True)
    report.add_argument("font", metavar="TTF", help="font file")

    generate = subparsers.add_parser("generate")
    generate.add_argument(
        "--suite",
        help="Test suite to update/create (defaults to test.json)",
        metavar="JSON",
        default="test.json",
    )
    generate.add_argument(
        "--language",
        help="Language to pass to shaper",
    )
    generate.add_argument(
        "--only", action="store_true", help="Add \"'only': FONT\" to JSON test cases"
    )
    generate.add_argument(
        "--restrict-unicodes",
        help="Restrict unicodes to the given range(s, comma separated)",
        metavar="RANGE",
    )
    generate.add_argument(
        "--just-blobs",
        action="store_true",
        help="Only use glyph sequences known to trigger rules",
    )
    generate.add_argument(
        "--no-dotted-circle",
        action="store_true",
        help="Don't add tests with dotted circles",
    )
    generate.add_argument(
        "--string-length",
        type=int,
        default=5,
        help="Maximum string length",
    )
    generate.add_argument("font", metavar="TTF", help="font file")
    args = parser.parse_args(args)


    def restrict(unicodes, range_arg):
        allowable = set()
        ranges = range_arg.split(",")
        for r in ranges:
            m = re.match(r"\s*([0-9A-Fa-f]+)-([0-9A-Fa-f]+)", r)
            if not m:
                raise ValueError(f"Could not understand range {r}")
            for cp in range(int(m[1], 16), int(m[2], 16) + 1):
                allowable.add(chr(cp))
        return set(allowable) & set(unicodes)


    font = TTFont(args.font)
    ff = unparse(font)
    bbfont = load(args.font)
    num_routines = 0
    num_rules = 0


    # Monkeypatch shaperLib functions
    def wrap_do_apply(fn):
        def result(*args, **kwargs):
            fn.__self__.applied = True
            fn.__self__.parent.applied = True
            return fn(*args, **kwargs)

        return result


    for r in ff.routines:
        r.applied = False
        num_routines += 1
        for rule in r.rules:
            rule.applied = False
            rule.parent = r
            rule._do_apply = wrap_do_apply(rule._do_apply)
            num_rules += 1


    def count_triggered(ff):
        num_triggered_routines = 0
        num_triggered_rules = 0
        for r in ff.routines:
            if r.applied:
                num_triggered_routines += 1
            for rule in r.rules:
                if rule.applied:
                    num_triggered_rules += 1
        return num_triggered_routines, num_triggered_rules


    num_triggered_routines = 0
    num_triggered_rules = 0

    shaper = Shaper(ff, bbfont)

    unicodes = list(font.getBestCmap().keys())

    dotted_circle = font.getBestCmap().get(0x25CC)

    if args.cmd == "generate":
        # Remove those not involved in rules?
        # Complex shapers may mess this up?
        involved = set()
        reversecmap = font["cmap"].buildReversed()

        blobs = []
        for r in ff.routines:
            try:
                involved = involved | r.involved_glyphs
            except Exception:
                pass
            for rule in r.rules:
                if isinstance(rule, fontFeatures.Attachment):
                    fullinput = [list(rule.bases.keys())] + [list(rule.marks.keys())]
                else:
                    fullinput = (
                        rule.precontext
                        + getattr(rule, "input", [])
                        + getattr(rule, "glyphs", [])
                        + rule.postcontext
                    )
                allowable = []
                for slot in fullinput:
                    this_slot = []
                    for x in slot:
                        if x in reversecmap:
                            this_slot.extend([chr(c) for c in reversecmap[x]])
                    allowable.append(this_slot)
                if all(allowable):
                    blobs.extend(["".join(blob) for blob in itertools.product(*allowable)])

        unicodes = [c for c in unicodes if font.getBestCmap()[c] in involved]
        unicodes = [chr(c) for c in unicodes]
        if args.restrict_unicodes:
            unicodes = list(restrict(unicodes, args.restrict_unicodes))
        if args.just_blobs:
            unicodes = []
        unicodes.extend(blobs)


    rule = tqdm.tqdm(
        total=num_rules,
        position=1,
        colour="green",
        desc="Rules  ",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
    )
    routine = tqdm.tqdm(
        total=num_routines,
        position=2,
        colour="yellow",
        desc="Lookups",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
    )
    vh = Vharfbuzz(args.font)


    def run_a_test(string, tests=None, output=True):
        global num_triggered_routines
        global num_triggered_rules
        buf = Buffer(bbfont, unicodes=string)#,language=args.language)
        try:
            shaper.execute(buf)
        except Exception:
            return False

        if dotted_circle and args.no_dotted_circle:
            # Check HB, FF shaper doesn't always add dotted circles
            buf2 = vh.shape(string)
            if dotted_circle in vh.serialize_buf(buf2):
                return False

        new_triggered_routines, new_triggered_rules = count_triggered(ff)
        if (
            new_triggered_routines > num_triggered_routines
            or new_triggered_rules > num_triggered_rules
        ):
            if output:
                routine.write(string)
            if tests is not None:
                tests.append({"input": string})
            rule.n = 0
            rule.update(new_triggered_rules)
            routine.n = 0
            routine.update(new_triggered_routines)
        num_triggered_rules = new_triggered_rules
        num_triggered_routines = new_triggered_routines
        return new_triggered_rules == num_rules  # Done?


    tests = []
    suite = {"tests": []}
    if args.suite and os.path.exists(args.suite):
        suite = json.load(open(args.suite))
        if "tests" not in suite:
            suite["tests"] = []
        for t in suite["tests"]:
            if "only" in t and os.path.basename(args.font) != t["only"]:
                continue
            run_a_test(t["input"], tests=None, output=False)

    if args.cmd == "report":
        sys.exit(0)

    new_tests = []

    try:
        while True:
            string = "".join(
                random.choices(unicodes, k=random.randint(2, args.string_length))
            )
            if run_a_test(string, tests=new_tests, output=True):
                break
    except KeyboardInterrupt as e:
        pass

    fh = open(args.suite, "w")
    params = {}
    if args.language:
        params["language"] = args.language
    # Use HB for gold-standard output
    for test in new_tests:
        buf = vh.shape(test["input"],parameters=params)
        test["expectation"] = vh.serialize_buf(buf)
        if args.only:
            test["only"] = os.path.basename(args.font)
        test["note"] = "Added by SIESTA"
        for k,v in params.items():
            test[k] = v

    suite["tests"].extend(new_tests)
    json.dump(suite, fh, sort_keys=True, indent=4, ensure_ascii=False)

    print("The following lookups were not triggered:")
    for r in ff.routines:
        if not r.applied:
            print(r.asFea())
    sys.exit(0)

if __name__ == "__main__":
    main()