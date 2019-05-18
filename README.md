# Unicode Codepoints Parser

## description
script for creating codepoint-to-name maps from ICU unicode codepoint data. its primary purpose is the construction of, optionally customised, emoji codepoint maps

this project was born out of a script originally found in the [emo](https://github.com/cmstrickland/emo) project, used for this very same purpose

## usage
briefly, the following command downloads and generates the latest supported emoji set
```sh
    $ ./ucp.py -d -g -o   # output at 'codepoints/unicode-12/unicode-12.map
    $ ./ucp.py -d -g > results
```
verbosely.. the raw datasets can currently be found under the following root url:

  https://www.unicode.org/Public/

e.g.

  https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt
  https://www.unicode.org/Public/12.0.0/ucd/UnicodeData.txt
  https://www.unicode.org/Public/emoji/5.0/emoji-data.txt

these can be downloaded using this script's `--download` and optionally `--target` options with file(s) being written to `codepoints/unicode-version/upstream` subdirectories

the `--generate` option can then be used to collate these files into a single, leaner, `unicode-version.raw` file prior to final filtering

the `--matchsets` option can be used to adjust the default builtin filter which is called `_emoji2_`. `--matchsets` takes a comma delimited list builtin matchset name(s) and/or arbitrary match strings. '[+]/-' prefixes can be used to designate whether the matchset is a positive (default) / negative (blacklist) filter. the negative filter is applied before the positive filter.

```sh
usage: ucp.py [-h] [-lt] [-t [TARGET]] [-d] [-u [URL_ROOT]] [-g] [-s SOURCE]
              [-ms MATCHSETS] [-o] [-v]

Unicode Codepoints Parser

optional arguments:
  -h, --help            show this help message and exit
  -lt, --list-targets   list unicode versions available for targeting
  -t [TARGET], --target [TARGET]
                        unicode version to target
  -d, --download        download ICU codepoints data
  -u [URL_ROOT], --url [URL_ROOT]
                        override default root url for ICU codepoints data
  -g, --generate        generate the codepoints map
  -s SOURCE, --source SOURCE
                        local path to either an ICU codepoints upstream data
                        set ora collated '.raw' file (default: stdin)
  -ms MATCHSETS, --matchsets MATCHSETS
                        comma delimited list of pre-defined matchsets and/or
                        arbitrary match strings. '[+]/-' prefixes can be used
                        todesignate the matchset as a positive/negative filter
  -o, --dump            dump the generated map to the standard target version
                        location and disable the default writing to stdout
  -v, --verbose         increase the level of information output
```

## examples
### dowloading
```sh
    $ ./ucp.py -d -t unicode-10
    # downloading ICU codepoints for 'unicode-10'

    $ ls -a1R codepoints/unicode-10/upstream
    codepoints/unicode-10/upstream:
    .
    ..
    emoji-data.txt
    emoji-sequences.txt
    emoji-variation-sequences.txt
    emoji-zwj-sequences.txt
    UnicodeData.txt
```
### generating maps
```sh
    $ ./ucp.py -o -g -ms "_emoji_" -t unicode-6 -s codepoints/unicode-6/unicode-6.raw
    mapped 1006 codepoints

    $ ./ucp.py -o -g -ms "_emoji_,flag" -t unicode-6 -s codepoints/unicode-6/unicode-6.raw
    mapped 1015 codepoints

    $ ./ucp.py -o -g -ms "_emoji_,-flag" -t unicode-6 -s codepoints/unicode-12/unicode-12.raw
    mapped 997 codepoints

    $ ./ucp.py -o -g -ms "_emoji2_" -s codepoints/unicode/unicode-12.raw
    # generating codepoints map
    mapped 5887 codepoints

    $ ./ucp.py -o -g -ms "_emoji2_,0x1f01" -s codepoints/unicode-12/unicode-12.raw
    # generating codepoints map
    mapped 5888 codepoints

    $ ./ucp.py -o -g -ms "_emoji2_,0x1f0" -s codepoints/unicode-12/unicode-12.raw
    # generating codepoints map
    mapped 5913 codepoints

    ./ucp.py -o -g -ms "_emoji2_,-church" -s codepoints/unicode-12/unicode-12.raw
    # generating codepoints map
    mapped 5886 codepoints

    ./ucp.py -o -g -ms "_emoji_" -s codepoints/unicode-12/unicode-12.raw
    # generating codepoints map
    mapped 1024 codepoints

    ./ucp.py -o -g -ms "_emoji_,flag" -s codepoints/unicode-12/unicode-12.raw
    # generating codepoints map
    mapped 1297 codepoints
```

## contributors
- cmstrickland
- elbeardmorez
