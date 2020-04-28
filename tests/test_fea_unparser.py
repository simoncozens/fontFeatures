from fontFeatures import Substitution
from fontFeatures.feaLib import FeaUnparser

import unittest
import re
class TestFeaUnparser(unittest.TestCase):

  def assertSufficientlyEqual(self, s1, s2):
    def alltrim(a):
      a = re.sub("#.*","",a)
      a = re.sub("\\s+"," ",a)
      return a.strip()
    self.assertEqual(alltrim(s1), alltrim(s2))

  def test_empty_lookup(self):
    tests = [
      "lookup dummy { } dummy;",
      "lookup dummy1 { } dummy1; lookup dummy2 { } dummy2;",
    ]

    for s in tests:
      self.assertSufficientlyEqual(FeaUnparser(s).ff.asFea(), s)

  def test_single_subst(self):
    tests = [
      "lookup dummy { sub a by b; } dummy;",
      "lookup dummy { sub x a' y by b; } dummy;",
      "lookup dummy { sub [a b] by [d e]; } dummy;",
      "lookup dummy { sub [a b]' y by [d e]; } dummy;",
      "lookup dummy { sub one two [a b]' y by [d e]; } dummy;",
      "lookup dummy { sub [one two] [a b]' y by [d e]; } dummy;",
    ]

    for s in tests:
      self.assertSufficientlyEqual(FeaUnparser(s).ff.asFea(), s)

  def test_multiple_subst(self):
    tests = [
      "lookup dummy { sub f_f_i by f f i; } dummy;",
      "lookup dummy { sub f_f_i' x by f f i; } dummy;",
      "lookup dummy { sub [a b] f_f_i' x by f f i; } dummy;",
    ]

    for s in tests:
      self.assertSufficientlyEqual(FeaUnparser(s).ff.asFea(), s)

  def test_alternate_subst(self):
    tests = [
      "lookup dummy { sub ampersand from [ampersand.1 ampersand.2 ampersand.3]; } dummy;",
      "lookup dummy { sub x ampersand' from [ampersand.1 ampersand.2 ampersand.3]; } dummy;"
      # Did you know you could do that?
    ]

    for s in tests:
      self.assertSufficientlyEqual(FeaUnparser(s).ff.asFea(), s)

  def test_ligature_subst(self):
    tests = [
      "lookup dummy { sub [one one.oldstyle] [slash fraction] [two two.oldstyle] by onehalf; } dummy;",
      "lookup dummy { sub [o u] f' f' by f_f; } dummy;",
      "lookup dummy { sub [e e.begin]' t' c by ampersand; } dummy;"
    ]

    for s in tests:
      self.assertSufficientlyEqual(FeaUnparser(s).ff.asFea(), s)

  def test_chain_subst(self):
    tests = [
      "lookup dummy { sub a by b; } dummy; lookup chain { sub a' lookup dummy; } chain; ",
      "lookup dummy { sub a by b; } dummy; lookup chain { sub x [one two] a' lookup dummy b' lookup dummy; } chain; ",
    ]

    for s in tests:
      self.assertSufficientlyEqual(FeaUnparser(s).ff.asFea(), s)

  def test_ignore(self):
    tests = [
      "lookup dummy { ignore sub a d' d; } dummy; ",
    ]

    for s in tests:
      self.assertSufficientlyEqual(FeaUnparser(s).ff.asFea(), s)

  def test_feature(self):
    tests = [
      "feature calt { sub a by b; sub c by d; } calt; ",
    ]

    for s in tests:
      self.assertSufficientlyEqual(FeaUnparser(s).ff.asFea(), s)

