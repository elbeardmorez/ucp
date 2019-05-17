#!/usr/bin/env python
from __future__ import print_function
import argparse
import os
import sys
try:
    import urllib.request as http  # python 3
except ImportError:
    import urllib as http  # python 2
import fileinput
import re

cwd = os.path.dirname(sys.argv[0])
url_default = "https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt"
emoticon_match = re.compile('^1F[3456][0-9ABCDEF]{2}')


def generate(source):
    print("# generating codepoints map", file=sys.stderr)
    print("src: %r" % ("[stdin]" if source == '-'
                                 else source), file=sys.stderr)

    map_count = 0
    for line in fileinput.input(source):
        if emoticon_match.match(line) :
            (cp,desc) = line.split(';')[0:2]
            desc = desc.lower().replace(' ','-')
            cp = cp.lower()
            print('\t"{0}" : 0x{1},'.format(desc,cp))
            map_count += 1
    print("# mapped %d codepoints" % (map_count), file=sys.stderr)


def download(url, target):
    print("# downloading ICU codepoints", file=sys.stderr)

    print("src: %r" % (url), file=sys.stderr)
    print("dest: %r" % (target), file=sys.stderr)

    f = None
    try:
        f = open(target, 'w')
        f.close()
    except Exception as e:
        print("cannot write to target file: %r" % (target), file=sys.stderr)
    try:
        http.urlretrieve(url, target)
    except Exception as e:
        print("download failed:\n\n" + e, file=sys.stderr)
        sys.exit(1)


parser = argparse.ArgumentParser(
    argument_default='-h',
    description='Unicode Codepoints Parser')
parser.add_argument(
    '-g', '--generate', action='store_const',
    const=True, default=False,
    help="generate the codepoints map")
parser.add_argument(
    '-d', '--download', action='store_const',
    const=True, default=False,
    help="download latest ICU codepoints data blob")
parser.add_argument(
    '-u', '--url', dest='url', nargs='?',
    default=url_default,
    help="set URL for ICU codepoints data blob")
parser.add_argument(
    '-s', '--source', type=str, default='-',
    help="ICU codepoints data blob (default: stdin)")

if not sys.argv[1:]:
    parser.print_help(sys.stderr)
    exit(0)

source = args.source
if args.download:
    target = os.path.join(cwd, 'codepoints', 'unicode-latest.raw')
    download(args.url, target)
    source = target
if args.generate:
    sys.argv = [sys.argv[0]]
    generate(source)
