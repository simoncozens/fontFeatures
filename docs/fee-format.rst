Writing Font Feature Code in the FEE Language
=============================================

FEE (Font Engineering language with Extensibility) is a language for
creating font feature code. One of the major differences between FEE
and Adobe's AFDKO feature language is that FEE is extensible via
Python plugins. These plugins have access to the glyph set, the glyph
metrics and the path information of glyphs in the font, allowing them
to emit intelligent and responsive collections of rules automatically.

Currently fontFeatures does not have its own OpenType binary compiler,
so FEE code is generally converted to Adobe FEA syntax using the
``fee2fea`` preprocessor::

		% echo "DefineClass @short_beh = /^BE/ and (width<200);" > test.fee
		% fee2fea MyFont.ttf test.fee
		@short_beh = [BEi1 BEi12 BEi2 BEi3 BEi9 BEm5 BEmsd4 BEmsd5];

Because FEE needs access to font data in order to apply its rules, a
font file is obviously needed as input to the program. A common technique
is to create a "dummy" font using an empty features file, run the
preprocessor, and then create the final font using the generated features::

	  touch features.fea
    fontmake --master-dir . -g MyFont.glyphs -o ttf --no-production-names
    mv master_ttf/MyFont-Regular.ttf master_ttf/MyFont-Dummy.ttf
    fee2fea -O0 master_ttf/MyFont-Dummy.ttf features.fee > features.fea
    fontmake --master-dir . -g MyFont.glyphs -o ttf

Overview of the FEE language
----------------------------

FEE statements consist of a *verb* followed by *arguments* and terminated
with a semicolon (``;``). Each verb defines their own set of arguments,
and this means that there is considerable flexibility in how the arguments
appear. For example, the ``Anchors`` statement takes a glyph name, followed
by an open curly brace (``{``), a series of anchor name / anchor position
pairs, and a close curly brace (``}``) - but no other verb has this pattern.
(Plugin writers are encouraged to keep the argument syntax simple and
intuitive.)

In general, amount and type of whitespace is not significant so long
as arguments are separated unambiguously, and comments may be inserted
between sentences in the usual form (``# ignored to end of line``).

Here is a simple FEE file::

	DefineClass @comma = [uni060C uni061B];
	Feature ss08 {
		Substitute @comma -> @comma.alt;
	};

The meaning should be fairly obvious to users of Adobe feature syntax,
but some features (particularly the use of "dot suffixing" to create
a synthetic class) will be unfamiliar. We'll start by discussing how
to address a set of glyphs within the FEE language before moving on to
the verbs that are available.

Glyph Selectors
---------------

A *glyph selector* is a way of specifying a set of glyphs in the FEE language. There are various forms of glyph selector:

- A single glyph name: ``a``
- An class name: ``@lc``
- An inline class: ``[a e i o u]`` (Inline classes may also contain class names, but may *not* contain ranges.)
- A regular expression: ``/\.sc/``. All glyph names in the font which match the expression will be selected. (This is another reason why FEE needs the font beforehand.)

Any of these forms may be followed by zero or more *suffixing operations*
or *desuffixing operations*. A suffixing operation begins with a period,
and adds the period plus its argument to the end of any glyph names matched
by the selector. In the example above ``@comma.alt``, the glyphs selected
would be ``uni060C.alt`` and ``uni060C.alt``.

A desuffixing operation, on the other hand, begins with a tilde, and *removes* the dot-suffix from the name of all glyphs matched by the selector.
For example, the glyph selector ``/\.sc$/~sc`` turns out to be a useful
way of identifying all glyphs which have a ``.sc`` suffix and turning
them back into their bare forms, suitable for the left-hand side of a
substitution operation. Now you don't have to keep track of which
glyphs you have small-caps forms of; you can select the list of small
caps glyphs, and turn that back into the unsuffixed form::

		Substitute /\.sc$/~sc -> /\.sc$/;
		# Equivalent to "Substitute [a b c ...] -> [a.sc b.sc c.sc ...];"

Standard plugins
----------------

In FEE, *all* verbs are provided by Python plugins. There are no "built-in"
verbs. However, the following plugins are automatically loaded and their
verbs are always available.

.. automodule:: fontFeatures.feeLib.ClassDefinition
.. automodule:: fontFeatures.feeLib.Feature
.. automodule:: fontFeatures.feeLib.LoadPlugin
.. automodule:: fontFeatures.feeLib.Routine
.. automodule:: fontFeatures.feeLib.Substitute
.. automodule:: fontFeatures.feeLib.Position

Optional plugins
----------------

.. automodule:: fontFeatures.feeLib.Anchors
.. automodule:: fontFeatures.feeLib.Arabic
.. automodule:: fontFeatures.feeLib.AvoidCollision
.. automodule:: fontFeatures.feeLib.BariYe
.. automodule:: fontFeatures.feeLib.FontEngineering
.. automodule:: fontFeatures.feeLib.IfCollides
.. automodule:: fontFeatures.feeLib.IMatra
.. automodule:: fontFeatures.feeLib.KernToDistance

Writing your own plugins
------------------------
