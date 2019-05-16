#!/usr/bin/env python
from __future__ import print_function
import argparse
import sys
import fileinput
import re

emoticon_match = re.compile('^1F[3456][0-9ABCDEF]{2}')


def generate(source):
    print("# generating codepoints map", file=sys.stderr)
    print("src: %r" % ("[stdin]" if source == '-'
                                 else source), file=sys.stderr)

    for line in fileinput.input(source):
        if emoticon_match.match(line) :
            (cp,desc) = line.split(';')[0:2]
            desc = desc.lower().replace(' ','-')
            cp = cp.lower()
            print('\t"{0}" : 0x{1},'.format(desc,cp))


parser = argparse.ArgumentParser(
    argument_default='-h',
    description='Unicode Codepoints Parser')
parser.add_argument(
    '-g', '--generate', action='store_const',
    const=True, default=False,
    help="generate the codepoints map")
parser.add_argument(
    '-s', '--source', type=str, default='-',
    help="ICU codepoints data blob (default: stdin)")

args = parser.parse_args(None if sys.argv[1:] else ['-h'])

source = args.source
if args.generate:
    sys.argv = [sys.argv[0]]
    generate(source)
