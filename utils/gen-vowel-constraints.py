#!/usr/bin/env python3

"""Generator of the function to prohibit certain vowel sequences.

It creates ``_hb_preprocess_text_vowel_constraints``, which inserts dotted
circles into sequences prohibited by the USE script development spec.
This function should be used as the ``preprocess_text`` of an
``hb_ot_complex_shaper_t``.

usage: ./gen-vowel-constraints.py ms-use/IndicShapingInvalidCluster.txt

"""

import collections
import youseedee

def write (s):
    sys.stdout.flush ()
    sys.stdout.buffer.write (s.encode ('utf-8'))
import sys

if len (sys.argv) != 2:
    sys.exit (__doc__)

script_order = {}
scripts = {}

for start, end,script in youseedee.parse_file_ranges("Scripts.txt"):
    for u in range (start, end + 1):
        scripts[u] = script
    if script not in script_order:
        script_order[script] = start

class ConstraintSet (object):
    """A set of prohibited code point sequences.

    Args:
        constraint (List[int]): A prohibited code point sequence.

    """
    def __init__ (self, constraint):
        # Either a list or a dictionary. As a list of code points, it
        # represents a prohibited code point sequence. As a dictionary,
        # it represents a set of prohibited sequences, where each item
        # represents the set of prohibited sequences starting with the
        # key (a code point) concatenated with any of the values
        # (ConstraintSets).
        self._c = constraint

    def add (self, constraint):
        """Add a constraint to this set."""
        if not constraint:
            return
        first = constraint[0]
        rest = constraint[1:]
        if isinstance (self._c, list):
            if constraint == self._c[:len (constraint)]:
                self._c = constraint
            elif self._c != constraint[:len (self._c)]:
                self._c = {self._c[0]: ConstraintSet (self._c[1:])}
        if isinstance (self._c, dict):
            if first in self._c:
                self._c[first].add (rest)
            else:
                self._c[first] = ConstraintSet (rest)

    @staticmethod
    def _indent (depth):
        return ('    ' * depth)

    @staticmethod
    def _cp_accessor(index):
        if index:
            return "buffer.items[i+{}].codepoint".format(index)
        return "buffer.items[i].codepoint"

    def __str__ (self, index=0, depth=2):
        s = []
        indent = self._indent (depth)

        if isinstance (self._c, list):
            if len (self._c) == 0:
                assert index == 2, 'Cannot use `matched` for this constraint; the general case has not been implemented'
                s.append ('{}matched = True\n'.format (indent))
            elif len (self._c) == 1:
                assert index == 1, 'Cannot use `matched` for this constraint; the general case has not been implemented'
                s.append ('{}matched = 0x{:04X} == {}\n'.format (indent, next (iter (self._c)), self._cp_accessor(index)))
            else:
                s.append ('{}if (0x{:04X} == {} and\n'.format (indent, self._c[0], self._cp_accessor(index)))
                if index:
                    s.append ('{}i + {} < len(buffer.items)-1 and\n'.format (self._indent (depth + 2), index + 1))
                for i, cp in enumerate (self._c[1:], start=1):
                    s.append ('{}0x{:04X} == {}{}\n'.format (
                        self._indent (depth + 2), cp, self._cp_accessor(index + i), '):' if i == len (self._c) - 1 else 'and')
                    )
                s.append ('{}matched = True\n'.format (self._indent (depth + 1)))
        else:
            cases = collections.defaultdict (set)
            for first, rest in sorted (self._c.items ()):
                cases[rest.__str__ (index + 1, depth + 2)].add (first)
            for body, labels in sorted (cases.items (), key=lambda b_ls: sorted (b_ls[1])[0]):
                if len(labels) == 1:
                    s.append (self._indent (depth + 1) + "if {} == 0x{:04X}:\n".format(self._cp_accessor(index), list(labels)[0]))
                else:
                    points = ", ".join(['0x{:04X}'.format(cp) for cp in sorted(labels)])
                    s.append (self._indent (depth + 1) + "if {} in [{}]:\n".format(self._cp_accessor(index), points))
                s.append (body)
        return ''.join (s)

constraints = {}
with open (sys.argv[1], encoding='utf-8') as f:
    constraints_header = []
    while True:
        line = f.readline ().strip ()
        if line == '#':
            break
        constraints_header.append(line)
    for line in f:
        j = line.find ('#')
        if j >= 0:
            line = line[:j]
        constraint = [int (cp, 16) for cp in line.split (';')[0].split ()]
        if not constraint: continue
        assert 2 <= len (constraint), 'Prohibited sequence is too short: {}'.format (constraint)
        script = scripts[constraint[0]]
        if script in constraints:
            constraints[script].add (constraint)
        else:
            constraints[script] = ConstraintSet (constraint)
        assert constraints, 'No constraints found'

print ('# The following functions are generated by running:')
print ('# %s ms-use/IndicShapingInvalidCluster.txt' % sys.argv[0])

print("""
from fontFeatures.shaperLib.Buffer import BufferItem

DOTTED_CIRCLE = 0x25CC

def _insert_dotted_circle(buf, index):
    dotted_circle = BufferItem.new_unicode(DOTTED_CIRCLE)
    buf.items.insert(index, dotted_circle)

""")

print ('def preprocess_text_vowel_constraints(buffer):')

for script, constraints in sorted (constraints.items (), key=lambda s_c: script_order[s_c[0]]):
    print(f'    if buffer.script == "{script}":')
    print ('        i = 0')
    print ('        while i < len(buffer.items)-1:')
    print ('            matched = False')
    write (str (constraints))
    print ('            i = i + 1')
    print ('            if matched: _insert_dotted_circle(buffer, i)')

