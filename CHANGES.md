CHANGES
=======

1.0.4

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
