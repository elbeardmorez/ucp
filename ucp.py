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
map_expressions_builtin = {
   '_builtin_best_': [0, re.compile('^1f[3-6][0-9a-f]{2}')],
   '_builtin_full_': [0, re.compile('^1f[0-6][0-9a-f]{2}')]
}
map_expressions_negative = []
map_expressions_positive = []


def parse_matchsets(matchsets):
    matchsets = matchsets.split(',')
    for m in matchsets:
        m = m.strip()
        print("parsing matchset: %r" % (m), file=sys.stderr)
        if m == "":
            continue  # discard empty
        map_expressions_target = map_expressions_positive
        if m[0:1] == "-":
            map_expressions_target = map_expressions_negative
            m = m[1:]
        elif m[0:1] == "+":
            m = m[1:]
        if m in map_expressions_builtin:
            map_expressions_target\
                .append([m, *map_expressions_builtin[m]])
            continue
        match_on = 0  # codepoint
        if m[0:2] == '0x':
            m = m[2:]
        else:
            match_on = 1  # description
        map_expressions_target.append(
            ['custom', match_on, re.compile(".*%s.*" % (re.escape(m)))])


def generate(source):
    print("# generating codepoints map", file=sys.stderr)
    print("src: %r" % ("[stdin]" if source == '-' else source),
          file=sys.stderr)

    # build matches
    matches = []
    for line in fileinput.input(source):
        (cp, desc) = line.split(';')[0:2]
        desc = desc.lower().replace(' ', '-')
        cp = cp.lower()
        match = 0
        for _, match_on, rx in map_expressions_negative:
            if (match_on == 0 and rx.match(cp)) or \
               (match_on == 1 and rx.match(desc)):
                match = 1
                break
        if match == 1:
            continue  # negative match
        for _, match_on, rx in map_expressions_positive:
            if (match_on == 0 and rx.match(cp)) or \
               (match_on == 1 and rx.match(desc)):
                match = 1
                break
        if match == 1:
            matches.append([cp, desc])
    print("# mapped %d codepoints" % (len(matches)), file=sys.stderr)

    # build map file
    for cp, desc in matches:
        print('0x{0};{1}'.format(cp, desc))


def download(url, target):
    print("# downloading ICU codepoints", file=sys.stderr)

    print("src: %r" % (url), file=sys.stderr)
    print("dest: %r" % (target), file=sys.stderr)

    f = None
    try:
        f = open(target, 'w')
        f.close()
    except Exception:
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
    '-ms', '--matchsets', dest='matchsets', nargs='?',
    default='_builtin_best_',
    help="comma delimited list of pre-defined matchsets" +
         " and/or arbitrary match strings")
parser.add_argument(
    '-s', '--source', type=str, default='-',
    help="ICU codepoints data blob (default: stdin)")

if not sys.argv[1:]:
    parser.print_help(sys.stderr)
    exit(0)

args = parser.parse_args()

source = args.source
if args.download:
    target = os.path.join(cwd, 'codepoints', 'unicode-latest.raw')
    download(args.url, target)
    source = target
if args.generate:
    if args.matchsets:
        try:
            parse_matchsets(args.matchsets)
        except Exception as e:
            print("error: %s" % (e), file=sys.stderr)
            exit(1)
    sys.argv = [sys.argv[0]]
    generate(source)
