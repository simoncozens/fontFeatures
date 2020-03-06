# Notes on a new feature file format

## Glyph class logic

I want dot-suffixed glyph classes to be equivalent to suffixing each glyph:

  @alpha = [a b c d e f g h ...];

  @alpha.sc # Automatically expands to [a.sc b.sc c.sc ...]

I want to be able to dot-suffix ranges as well: `[a-z].sc`.

## Substitutions in general

I want $ to stand for the glyph name being substituted, and I want to be able to dot-suffix it:

    [a-z] -> $.sc;

In multiple substitutions I want numeric dollar variables just like awk:

    uni17D2 uni1780 -> $2.coeng

## Chaining contextual substitutions

Lookups are often used because many-to-many substitutions aren't expressable
directly. This is an artefact - the AFDKO format is being driven by the low-level representation of the GSUB table, not by what the user wants to express. Much better to enable many-to-many and let the compiler sort out the representation:

    a b c -> c b a;

The idea of prefix - input - suffix similarly drives the use of the quoted forms to mark the input, and it's another artefact. If we use dollar variables the compiler can figure out what is prefix and what is suffix:

    @kasra ayin.fina -> $1 tatweel $2;

    feature ccmp { @capitals @accents -> $1 $2.cap; }

I want to be able to express these substitutions hierarchically:

    kaf.init {
        mem.medi -> $1.KafMemInit $2.KafMemMedi;
        baa.medi alif.fina -> $1.KafBaaInit $2.KafBaaInit $3;
        heh.fina -> $1.KafHeh $2.KafHeh;
        lam.medi {
            mem.medi -> $1.KafLam $2.KafLamMemMedi $3.LamMemMedi;
            alif.fina -> $1.KafLam $2.KafLamAlif $3;
            _ -> $1.KafLam $2.KafLamMedi $3;
        }
    }

## Format 2 (glyph class based) substitutions

## Mark and base positioning

    anchors a {
        top <163 460>;
        bottom <162 0>;
        ogonek <262 -12>;
    }
    anchors e {
        top <173 422>;
        bottom <171 0>;
        ogonek <269 22>;
    }
    anchors acutecomb {
        _top <127 427>;
        top <124 604>;
    }
    anchors ogonekcomb {
        _ogonek <162 115>;
    }

    attach &ogonek &_ogonek;
    attach &top &_top;

## Variable fonts


## See also

https://github.com/silnrsi/pysilfont/blob/master/docs/feaextensions.md
https://github.com/davelab6/dancingshoes