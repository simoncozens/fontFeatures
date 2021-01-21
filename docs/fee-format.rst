.. _fee:

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
- A Unicode codepoint: ``U+1234`` (This will be mapped to a glyph in the font. If no glyph exists, an error is raised.)

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
.. automodule:: fontFeatures.feeLib.Conditional
.. automodule:: fontFeatures.feeLib.Feature
.. automodule:: fontFeatures.feeLib.LoadPlugin
.. automodule:: fontFeatures.feeLib.Routine
.. automodule:: fontFeatures.feeLib.Substitute
.. automodule:: fontFeatures.feeLib.Position
.. automodule:: fontFeatures.feeLib.Chain

Optional plugins
----------------

.. automodule:: fontFeatures.feeLib.Anchors
.. automodule:: fontFeatures.feeLib.Arabic
.. automodule:: fontFeatures.feeLib.BariYe
.. automodule:: fontFeatures.feeLib.FontEngineering
.. automodule:: fontFeatures.feeLib.IfCollides
.. automodule:: fontFeatures.feeLib.IMatra
.. automodule:: fontFeatures.feeLib.KernToDistance
.. automodule:: fontFeatures.feeLib.LigatureFinder
.. automodule:: fontFeatures.feeLib.MedialRa

Writing your own plugins
------------------------

The power of FEE comes from its extensibility, and that means the ability to
write your own plugins. A guiding principle of writing feature code in the
FEE language is that instead of *telling* the font specifically what to do
("move these two glyphs fifty units apart"), as much as possible you *query*
the font for information and then automatically *work out* the right thing to
do. This is done through writing "rules which write rules" in Python modules.

This takes a bit of work, but the end result should be that you have sets of
rules that you can carry from font to font without needing to rewrite them.

Let's take a look at a couple of sample plugins to see how they're constructed.

Parsley Grammars
^^^^^^^^^^^^^^^^

A fontFeatures plugin comes in two parts: the *grammar* and the *code*. Grammars
explain what kinds of arguments, and how many arguments, the verbs in the plugin
expect. Grammars are written in the notation used by the
`Parsley module <https://parsley.readthedocs.io/en/latest/tutorial.html>`_ so
you should start by reading its documentation (or, if you're like me, by picking
it up by looking at existing examples).

Our first plugin is going to be called ``CopyAnchors``, and it will copy all
anchors from glyphs in one glyph class to glyphs in another glyph class. What
do we want the call to this verb to look like? Probably something like ``CopyAnchors @gc1 @gc2;``. So the arguments to ``CopyAnchors`` will be two glyph selectors, separated by whitespace. Here's how we will start our plugin::

    GRAMMAR = """
    CopyAnchors_Args = glyphselector:fromglyphs ws glyphselector:toglyphs -> (fromglyphs, toglyphs)
    """
    VERBS = ["CopyAnchors"]

A ``GRAMMAR`` statement can contain multiple Parsley rules, but must have one
ending in ``_Args`` for each verb to be defined. The ``CopyAnchors_Args`` rule
takes two glyph selectors, separated by whitespace, and gives each of them a
variable name. It then uses these variable names to return a tuple. It is this
tuple which will be added to the arguments sent to the Python method which
implements the verb's functionality, which we'll look at in a moment.

Note that unfortunately Parsley grammars are quite fiddly, and the error
messages returned from Parsley when you get them wrong can be somewhat tricky
to understand. My advice is to start with small rules that work and build up.

You don't have to define all your rules from scratch, as we can see here.
``ws`` (which matches whitespace) is provided by Parsley as part of its
`built-in rules <https://parsley.readthedocs.io/en/latest/reference.html#built-in-parsley-rules>`_ and ``glyphselector`` is a rule
provided by FEE. Look at the ``basegrammar`` in the ``fontFeatures.feeLib``
module for the list of FEE's built-in rules.

Now we have the grammar, and also defined the ``VERBS`` that this module provides (don't forget that bit!), we can turn to implementation.

Verb implementations
^^^^^^^^^^^^^^^^^^^^

When a verb is "called" by a FEE file, this call is converted into a class
method call in Python, with the method called "action". So ``CopyAnchors
@gc1 @gc2;`` will appear in Python as ``CopyAnchors.action(parser, gc1, gc2)``.
(The FEE parser object also gets sent to the method, along with the arguments
we defined in our grammar. This gives us access to the font object, the
``fontFeatures`` object, and other stuff we might need.)

Let's set up our class, and then we'll talk about the content of those
arguments::

    class CopyAnchors:
        @classmethod
        def action(self, parser, fromglyphs, toglyphs):

Each Parsley rule returns a Python object, and it's up to you what that object
looks like. The ``integer`` rule, for instance, returns an integer, which is
quite helpful. You might expect the ``glyphselector`` rule to return a list of
glyph names, but it doesn't do that. There are a few reasons why not, but the
main one is that the parser doesn't know whether a ``glyphselector`` refers to
glyphs which are expected to be in the font already, or new glyphs that we're
going to be creating in the plugin. If it restricted itself to glyphs in the
font and we had a list of glyphs that didn't yet exist, it would return us an
empty list, which is not what we want. So ``glyphselector`` actually returns a
``GlyphSelector`` object, which must be resolved into a list of glyph names.
This is a common pattern you will see in a lot of FEE plugins::

          fromglyphs = fromglyphs.resolve(parser.fontfeatures, parser.font)
          toglyphs = toglyphs.resolve(parser.fontfeatures, parser.font)

(It needs the ``fontfeatures`` object so that it can resolve named class
references; it needs the ``font`` object for the list of glyphs in the font.)
If we were going to *create* the ``toglyphs`` we would tell ``resolve`` that
the glyphs don't need to exist yet::

          toglyphs = toglyphs.resolve(parser.fontfeatures, parser.font, mustExist=False)

Now we have a list of from-glyphs, a list of to-glyphs, a ``fontFeatures``
object, and the rest is easy: ``fontFeatures`` stores a dictionary of anchors
for each glyph, so we just copy them across::

          for (f, t) in zip(fromglyphs,toglyphs):
            parser.fontfeatures.anchors[t] = parser.fontfeatures.anchors[f]

Normally a FEE plugin would return a list of ``Routine`` objects, but we're
not creating any rules, so we just return an empty list::

          return []

And we're done. Now we'll look at a more involved plugin - one which inspects
the glyphs themselves, and emits some rules in response.

.. _imatra:

The IMatra Plugin
^^^^^^^^^^^^^^^^^

The IMatra plugin, described above, comes with fontFeatures. It matches the
"i" vowel sign in Devanagari to bases of the appropriate width. Let's see how
it works. First, we define the grammar. This is similar to the one above - just
three glyph selectors - but we use some constant symbols as a bit of "syntactic
sugar". Note that we only assign the glyph selectors to variables (and put them
into the return tuple), and not the syntactic sugar::

    GRAMMAR = """
    IMatra_Args = glyphselector:bases ws ':' ws glyphselector:matra ws '->' ws glyphselector:matras -> (bases,matra,matras)
    """

    VERBS = ["IMatra"]

We're going to need to know how wide all of our matras and bases are, and the
fontFeatures way to do this is to use the `get_glyph_metrics <https://glyphtools.readthedocs.io/en/latest/#glyphtools.get_glyph_metrics>`_ function from the `glyphtools <https://glyphtools.readthedocs.io/>`_ library::

    import fontFeatures
    from glyphtools import get_glyph_metrics

Now we're ready to write our action method, which will start with the usual
resolving of glyph selectors into glyph name lists::

    class IMatra:
        @classmethod
        def action(self, parser, bases, matra, matras):
            bases = bases.resolve(parser.fontfeatures, parser.font)
            matra = matra.resolve(parser.fontfeatures, parser.font)
            matras = matras.resolve(parser.fontfeatures, parser.font)

Let's think what we need to do now. We have a list of matras, with different
"overhangs" (negative RSBs). For each matra, we want a list of bases which this
matra best fits, and then we emit a set of substitution rules. First, we'll
create a dictionary to hold our "best fits" bases for each matra, and
arrange the list of matras into a list of (glyphname, overhang) tuples::

        matras2bases = {}
        matrasAndOverhangs = [
            (m, -get_glyph_metrics(parser.font, m)["rsb"]) for m in matras
        ]

Now we loop over the bases, and find the matra which has the smallest difference
between the base width and the matra overhang::

        for b in bases:
            w = get_glyph_metrics(parser.font, b)["width"]
            (bestMatra, _) = min(matrasAndOverhangs, key=lambda s: abs(s[1] - w))

And store this in the dictionary::

            if not bestMatra in matras2bases:
                matras2bases[bestMatra] = []
            matras2bases[bestMatra].append(b)

When the loop is finished and we have processed all the bases, we can now
turn the dictionary into a list of substitution rules. We want to emit rules
with this kind of form::

    Substitute { iMatra-deva } @bases_3 -> iMatra-deva.3;

i.e. the bases are the post-context for the matra substitution. This is how
we do it::

        rv = []
        for bestMatra, basesForThisMatra in matras2bases.items():
            rv.append(
                fontFeatures.Substitution(
                    [matra],
                    postcontext=[basesForThisMatra],
                    replacement=[[bestMatra]]
                )
            )

You may have noticed that ``bestMatra`` goes into a list of lists, but ``matra``
does not. It's good to think through why this is, because it will help you
understand fontFeatures rules. Resolving a glyph selector always returns a
list. So resolving the glyphselector ``matra`` returned a list of glyph names,
although probably that list had only one element. A substitution or positioning
rule defines its input as a list of glyph stream positions, each of which is a
list of glyph names that can match at this position. In essence, every element
of the glyph stream position list must be expressed as a "glyph class", even if
it is a one-element class. So the input will be::

    [
      # Glyph position 1:
      matra # We got a one-element list from `.resolve` e.g. ["iMatra-deva"]
    ]

For the postcontext, we want to match a glyph class. ``basesForThisMatra`` is
a list, so this is also fine::

    [
      # Glyph position 1:
      basesForThisMatra # e.g. [ "ga-deva", "gha-deva", ... ]
    ]

We want the replacement parameter to look the same: for each position in the
replacement glyph stream, a list of glyphs to be substituted. (This is because
``Substitution`` *also* supports "alternate" substitutions, in which glyph
position 1 will substitute multiple glyphs, and also because regularity is
good and leads to fewer surprises.) However, ``bestMatra`` is not a list,
but a single glyph; this is why we have to make it into one::

    [
      # Glyph position 1:
      [ "iMatra-deva.3" ]
    ]

Finally, all that remains to do is wrap up our list of substitution rules into
a routine, and return it::

        return [fontFeatures.Routine(rules=rv)]

In more complex scenarios, you may find yourself enumerating all the
combinations of glyphs within a sequence (the ``itertools.product`` function
is useful for this); checking whether a given set of glyphs causes a collision
when positioned (the :py:mod:`fontFeatures.jankyPOS` positioner and the `collidoscope <https://pypi.org/project/collidoscope/>`_ library may help you);
inspecting the paths and doing some sums based on them (:py:mod:`fontFeatures.pathUtils` and the `beziers <https://pypi.org/project/beziers/>`_ library are good for this).

To gain more understanding of what this might look like, try working through
the code of the :py:mod:`fontFeatures.feeLib.IfCollides` and
:py:mod:`fontFeatures.feeLib.BariYe` plugins.
