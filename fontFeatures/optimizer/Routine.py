from fontFeatures import Substitution, Positioning
import logging


class MoveLongCoverageToClassDefinition:
    level = 1

    def gensym(self, ff):
        if not "index" in ff.scratch:
            ff.scratch["index"] = 0
        ff.scratch["index"] = ff.scratch["index"] + 1
        return str(ff.scratch["index"])

    def replaceLongWithClasses(self, i, ff):
        for ix, gc in enumerate(i):
            if len(gc) > 5:
                classname = ff.getNamedClassFor(gc, "class" + self.gensym(ff))
                i[ix] = ["@" + classname]

    def apply(self, routine, ff):
        for rule in routine.rules:
            if isinstance(rule, Substitution):
                self.replaceLongWithClasses(rule.input, ff)
                self.replaceLongWithClasses(rule.precontext, ff)
                self.replaceLongWithClasses(rule.postcontext, ff)
                self.replaceLongWithClasses(rule.replacement, ff)
            if isinstance(rule, Positioning):
                self.replaceLongWithClasses(rule.glyphs, ff)
                self.replaceLongWithClasses(rule.precontext, ff)
                self.replaceLongWithClasses(rule.postcontext, ff)

        return []


class MergeMultipleSingleSubstitutions:
    level = 1

    def apply(self, routine, ff):

        _is_single_sub = (
            lambda rule: isinstance(rule, Substitution)
            and len(rule.input) == 1
            and len(rule.replacement) == 1
        )

        if len(routine.rules) < 2:
            return
        new_rules = [routine.rules[0]]
        for r in routine.rules[1:]:
            previous = new_rules[-1]
            if (
                _is_single_sub(r)
                and _is_single_sub(previous)
                and r.precontext == previous.precontext
                and r.postcontext == previous.postcontext
            ):
                new_rules.pop()
                new_rules.append(self.merge_two(previous, r))
            else:
                new_rules.append(r)
        routine.rules = new_rules
        # It's possible to get clever later with non-adjacent substitutions
        # if there's nothing in the middle that could affect the output

    def merge_two(self, first, second):
        assert len(first.input) == 1 and len(second.input) == 1
        assert len(first.replacement) == 1 and len(second.replacement) == 1
        assert first.precontext == second.precontext
        assert first.postcontext == second.postcontext
        firstmapping = {l: r for l, r in zip(first.input[0], first.replacement[0])}
        secondmapping = {l: r for l, r in zip(second.input[0], second.replacement[0])}
        for l, r in firstmapping.items():
            if r in secondmapping:
                firstmapping[l] = secondmapping[r]
        for l, r in secondmapping.items():
            if not (l in firstmapping):
                firstmapping[l] = r
        logger = logging.getLogger("fontFeatures")
        logger.info("Merging two adjacent single subs")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(first.asFea())
            logger.debug(second.asFea())
        address = first.address or second.address
        return Substitution(
            [list(firstmapping.keys())],
            [list(firstmapping.values())],
            address=address,
            precontext=first.precontext,
            postcontext=first.postcontext,
        )


optimizations = [
    MergeMultipleSingleSubstitutions,
    MoveLongCoverageToClassDefinition,  # Runs last
]
