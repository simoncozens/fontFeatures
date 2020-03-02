# Notes on a new feature file format

## Glyph class logic

I want dot-suffixed glyph classes to be equivalent to suffixing each glyph:

  @alpha = [a b c d e f g h ...];

  @alpha.sc # Automatically expands to [a.sc b.sc c.sc ...]
  # Can also be written as: [a-z].sc

## Format 2 (glyph class based) substitutions

## Chaining contextual substitutions

These are often used because many-to-many substitutions aren't expressable
directly.

    sub baa.init seen.medi by baa.init1 seen.init1;

## Variable fonts