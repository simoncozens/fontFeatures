# FEE — Font Engineering with Extensibility

The Font Engineering with Extensibility (FEE) language is implemented via a Python library, `fontFeatures`. This format improves over Adobe FEA (`.fea`) in several important ways, and compiles to FEA. In future, FEE also will compile to raw GPOS/GSUB binary tables.

## FEE Quickstart

Class definition is a time consuming element of writing FEA code. FEE allows regular expressions to be used to define classes; each glyph name in the font is tested against the regular expression, and the glyphs added:

```
DefineClass @sc = /\.sc$/;
```

Ran as:

```sh
fee2fea tests/LibertinusSans-Regular.otf test.fee
```

Results in:

```fea
@sc = [parenleft.sc parenright.sc bracketleft.sc bracketright.sc ...];
```

Simple replacement can be done as easily as:

```
DefineClass @sc = /\.sc$/;
DefineClass @sc_able = @sc~sc;

Feature smcp {
	Substitute @sc_able -> @sc;
};
```

Quite complex classes can be built. All the glyphs which have a smallcap and alternate form:

```
DefineClass @sc_and_alt_able = /.*/ and hasglyph(/$/ .alt) and hasglyph(/$/ .sc);
```

Returning:

```fea
@sc_and_alt_able = [h y germandbls];
```

FEE can even do substitutions impossible in FEA. For example:

```
DefineClass @digits =    U+0031=>U+0039; # this is range(U+0031, U+0039) inclusive
DefineClass @encircled = U+2474=>U+247C;

# Un-CJK parenthesize
Feature ss01 {
	Substitute @encircled -> parenleft @digits parenright;
};
```

Gives us:

```fea
feature ss01 {
    lookup Routine_1 {
            sub uni2474 by parenleft one parenright;
            sub uni2475 by parenleft two parenright;
            sub uni2476 by parenleft three parenright;
            sub uni2477 by parenleft four parenright;
            sub uni2478 by parenleft five parenright;
            sub uni2479 by parenleft six parenright;
            sub uni247A by parenleft seven parenright;
            sub uni247B by parenleft eight parenright;
            sub uni247C by parenleft nine parenright;
    } Routine_1;
} ss01;
```

FEE can do much more; see the [plugins documentation](https://fontfeatures.readthedocs.io/en/latest/fee-format.html#standard-plugins). Writing your own plugins is as simple as [defining its grammar, verb, and adding a class with an `action()` method](https://fontfeatures.readthedocs.io/en/latest/fee-format.html#writing-your-own-plugins).

## `fontFeatures` library

OpenType fonts are "programmed" using features, which are normally authored in Adobe's [feature file format](http://adobe-type-tools.github.io/afdko/OpenTypeFeatureFileSpecification.html). This like source code to a computer program: it's a user-friendly, but computer-unfriendly, way to represent the features.

Inside a font, the features are compiled in an efficient [internal format](https://simoncozens.github.io/fonts-and-layout/features.html#how-features-are-stored). This is like the binary of a computer program: computers can use it, but they can't do else anything with it, and people can't read it.

The purpose of this library is to provide a middle ground for representing features in a machine-manipulable format, kind of like the abstract syntax tree of a computer programmer. This is so that:

* features can be represented in a structured human-readable *and* machine-readable way, analogous to the XML files of the [Unified Font Object](http://unifiedfontobject.org/) format.
* features can be more directly authored by programs (such as font editors), rather than them having to output AFDKO feature file format.
* features can be easily manipulated by programs - for example, features from two files merged together, or lookups moved between languages.

> How is this different from fontTool's `feaLib`? I'm glad you asked. `feaLib` translates between the Adobe feature file format and a abstract syntax tree representing *elements of the feature file* - not representing the feature data. The AST is still "source equivalent". For example, when you code an `aalt` feature in feature file format, you might include code like `feature salt` to include lookups from another feature. But what's actually *meant* by that is a set of lookups. `fontFeatures` allows you to manipulate meaning, not description.

### Components

fontFeatures consists of the following components:

* `fontFeatures` itself, which is an abstract representation of the different layout operations inside a font.
* `fontFeatures.feaLib` (included as a mixin) which translates between Adobe feature syntax and fontFeatures representation.
* `fontFeatures.ttLib`, which translates between OpenType binary fonts and fontFeatures representation. (Currently only OTF -> `fontFeatures` is partially implemented; there is no `fontFeatures` -> OTF compiler yet.)
* `fontFeatures.feeLib` which parses a new, extensible format called FEE for font engineering.
* `fontFeatures.fontDameLib` which translate FontDame text files into fontFeatures objects.

And the following utilities:

* `fee2fea`: translates a FEE file into Adobe feature syntax.
* `otf2fea`: translates an OTF file into Adobe features syntax.
* `txt2fea`: translates a FontDame txt file into Adobe features syntax.
* `mergeFee`: takes an existing font, adds FEE rules to it, and writes it out again.
