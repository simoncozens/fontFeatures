import re

global classtype


def add_to_script_table(parsed, line):
    m = re.match("^(\w+)\s+(\w+)\s+(.*)$", line)
    lang = m[1] + "/" + m[2]
    parsed["all_languages"].append(lang)
    for f in m[3].split(", "):
        if not (f in parsed["script_applications"]):
            parsed["script_applications"][f] = []
        parsed["script_applications"][f].append(lang)


def add_to_feature_table(parsed, line):
    m = re.match("^(\w+)\s+(\w+)\s+(.*)$", line)
    parsed["features"].append(
        {
            "tag": m[2],
            "language": ",".join(parsed["script_applications"][m[1]]),
            "lookups": m[3].split(", "),
        }
    )
    for l in m[3].split(", "):
        # XXX Multiple languages
        if not l in parsed["lookups"]:
            parsed["lookups"][l] = {
                "feature": parsed["features"][-1]["tag"],
                "languages": [],
            }
        parsed["lookups"][l]["languages"].extend(parsed["script_applications"][m[1]])


def parse_lookup_header(parsed, line):
    m = re.match("^lookup\s+(\w+)\s+(.*)$", line)
    parsed["cur_lookup"] = m[1]
    if m[1] in parsed["lookups"]:
        parsed["lookups"][m[1]].update({"type": m[2], "flags": [], "rules": []})
    else:
        parsed["lookups"][m[1]] = {"type": m[2], "flags": [], "rules": []}


def get_class(parsed, cid, lookup):
    res = lookup["classes"][cid]
    if len(res) == 1:
        return res[0]
    if len(res) > 5:
        if not tuple(res) in parsed["classes"]:
            parsed["classes"].append(tuple(res))
        classname = "@class%i" % parsed["classes"].index(tuple(res))
        if classname in parsed["config"]:
            return parsed["config"][classname]
        return classname

    return res


def add_to_lookup(parsed, line):
    m = re.match("(\w+)\s+(yes|no)", line)
    lookup = parsed["lookups"][parsed["cur_lookup"]]
    if m:
        if m[2] == "yes":
            lookup["flags"].append(m[1])
        return
    if lookup["type"] == "single":
        m = re.match("([\w\.]+)\s+([\w\.]+)\n", line)
        lookup["rules"].append((m[1], m[2]))
    elif lookup["type"] == "multiple":
        m = re.match("([\w\.]+)\s+(.*)\n", line)
        lookup["rules"].append((m[1], m[2].split("\t")))
    elif lookup["type"] == "ligature":
        m = re.match("([\w\.]+)\s(.*)\n", line)
        lookup["rules"].append((m[2].split("\t"), m[1]))
    elif lookup["type"] == "context":
        if line.startswith("glyph"):
            m = line.rstrip().split("\t")
            context = m[1].split(", ")
            lookup["rules"].append({"context": context, "transformations": m[2:]})
        elif line.startswith("class"):
            # lookup["type"] == "class_context"
            m = line.rstrip().split("\t")
            context = [get_class(parsed, x, lookup) for x in m[1].split(", ")]
            lookup["rules"].append({"context": context, "transformations": m[2:]})
    else:
        # raise ValueError("Unsupported lookup type %s" % lookup["type"])
        pass


def add_to_class_definition(parsed, line):
    lookup = parsed["lookups"][parsed["cur_lookup"]]
    m = re.match("([\w\.]+)\s+(\d+)", line)
    if not m:
        print(line)
    if not "classes" in lookup:
        lookup["classes"] = {"0": []}
    if not m[2] in lookup["classes"]:
        lookup["classes"][m[2]] = []
    lookup["classes"][m[2]].append(m[1])


def apply_transformations(rule, parsed):
    context = list(rule["context"])
    transformations = {}
    for pos, lid in [t.split(", ") for t in rule["transformations"]]:
        transformations[int(pos) - 1] = parsed["lookups"][lid]

    for ix, c in reversed(list(enumerate(context))):
        if ix in transformations:
            # We have a transformation for this context
            lookup = transformations[ix]
            if (
                lookup["type"] == "single"
                and isinstance(context[ix], str)
                and not (context[ix].startswith("@"))
            ):
                for r in lookup["rules"]:
                    if context[ix] == r[0]:
                        context[ix] = r[1]
            elif (
                lookup["type"] == "multiple"
                and isinstance(context[ix], str)
                and not (context[ix].startswith("@"))
            ):
                for r in lookup["rules"]:
                    if context[ix] == r[0]:
                        if ix < len(context):
                            context = context[:ix] + r[1] + context[ix + 1 :]
                        else:
                            context = context[:ix] + r[1]
            else:
                lookupname = "Lookup" + str(lid)
                if lookupname in parsed["config"]:
                    lookupname = parsed["config"][lookupname]
                context[ix] = "%s($%i)" % (lookupname, ix + 1)

        else:
            context[ix] = "$%i" % (ix + 1)
        if isinstance(context[ix], list):
            context[ix] = "[%s]" % " ".join(context[ix])
    return context


def unparse(filename, config=None):
    state = "doing_nothing"
    count = 0
    parsed = {
        "all_languages": [],
        "script_applications": {},
        "features": [],
        "lookups": {},
        "classes": [],
    }
    if config:
        import json

        with open(config) as f:
            parsed["config"] = json.load(f)
    else:
        parsed["config"] = {}

    with open(filename) as file_in:
        for line in file_in:
            if line == "\n":
                continue
            elif line == "script table begin\n":
                state = "reading_script_table"
                continue
            elif line == "feature table begin\n":
                state = "reading_feature_table"
                continue
            elif line == "class definition begin\n":
                state = "reading_class_definition"
                continue
            elif line == "class definition end\n":
                state = "parsing_lookup"
                continue
            elif (
                line == "script table end\n"
                or line == "feature table end\n"
                or line == "lookup end\n"
            ):
                state = "doing_nothing"
                continue
            elif line.startswith("lookup"):
                parse_lookup_header(parsed, line)
                state = "parsing_lookup"
                continue

            if state == "reading_script_table":
                add_to_script_table(parsed, line)
            elif state == "reading_feature_table":
                add_to_feature_table(parsed, line)
            elif state == "parsing_lookup":
                add_to_lookup(parsed, line)
            elif state == "reading_class_definition":
                add_to_class_definition(parsed, line)
    # print(parsed["script_applications"])

    def glyphorclass(x):
        if isinstance(x, str):
            return x
        if len(x) == 1:
            return x[0]
        return "[%s]" % " ".join(x)

    def unparse_lookup_rules(lookup):
        for r in lookup["rules"]:
            if lookup["type"] == "single":
                rule = "Substitute %s -> %s" % (r[0], r[1])
            elif lookup["type"] == "multiple":
                rule = "Substitute %s -> %s" % (r[0], " ".join(r[1]))
            elif lookup["type"] == "ligature":
                rule = "Substitute %s -> %s" % (" ".join(r[0]), r[1])
            elif lookup["type"] == "context":
                context = " ".join([glyphorclass(x) for x in r["context"]])
                transformed = " ".join(apply_transformations(r, parsed))
                rule = " Substitute %s -> %s" % (context, transformed)

            else:
                raise ValueError("Undumpable lookup type %s" % lookup["type"])
            if "languages" in lookup and len(lookup["languages"]) != len(
                parsed["all_languages"]
            ):
                rule = rule + " <%s>" % ",".join(lookup["languages"])
            rule = rule + ";"
            print("\t" + rule)

    if len(parsed["classes"]) > 0:
        for ix, c in enumerate(parsed["classes"]):
            classname = "@class%i" % ix
            if classname in parsed["config"]:
                classname = parsed["config"][classname]
            print("DefineClass %s = [%s];" % (classname, " ".join(c)))

    for lid in sorted(parsed["lookups"].keys(), key=int):
        lookup = parsed["lookups"][lid]
        if "feature" in lookup:
            continue
        lookupname = "Lookup" + lid
        if lookupname in parsed["config"]:
            lookupname = parsed["config"][lookupname]
        print("Routine %s {" % lookupname)
        unparse_lookup_rules(lookup)
        print("}")

    lastFeature = None

    for lid in sorted(parsed["lookups"].keys(), key=int):
        lookup = parsed["lookups"][lid]
        if not ("feature" in lookup):
            continue
        if lookup["feature"] != lastFeature:
            if lastFeature is not None:
                print("}\n")
            print(lookup["feature"] + " {")
            lastFeature = lookup["feature"]
        print("\t# Lookup %i %s" % (int(lid), lookup["type"]))
        unparse_lookup_rules(lookup)
    print("}")
    return parsed
