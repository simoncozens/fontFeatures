from fontFeatures.tt2feaLib import unparse

def main():
    import sys
    from fontTools.ttLib import TTFont
    if not len(sys.argv) > 1:
        raise Exception('font-file argument missing')
    fontPath = sys.argv[1]
    font = TTFont(fontPath)
    ff = unparse(font)
    print(ff.asFea())

if __name__ == '__main__':
    main()