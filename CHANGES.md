CHANGES
=======

1.2.0

* Many fixes to language handling.

1.0.8

* Some fixes to pathUtils

1.0.7

* This was a maintenance release, fixing the requirements file.

1.0.6

* Make emitting the GDEF table optional
* Beginnings of a binary GSUB/GPOS emitter. Proof-of-concept only.
* Fix some mark-to-mark and mark-to-base unparsing bugs.

1.0.4

* New FEE quickstart in README
* New FEE verbs: IncludeFea, Swap, SetCategory.
* Support multiple substitution expansion in FEE.
* Only include "exported" glyphs in emitted rules.
* Fix to syntax of classnames (may include numbers).
* Automatically emit GDEF ClassDefinition statements.
* Support for variation tuples in Position rules.
* Temporarily disable optimizer.
* Add VIM syntax file.
* Buffers may contain items of BufferItem subclasses.
* Allow setting overshoot in MedialRa verb.

1.0.3

* Fix broken tests.

1.0.2

* Add hasglyph() predicate in glyph class definitions.
* Add class subtraction operation in glyph class definitions.
* Support variation stores in value records.

1.0.1

* Fix erroneous debug output in `Conditional`.
* Add rudimentary variable `Set` command.
* Unicode codepoints can be used in glyph selectors.
* Allow negative integers in comparisons.
