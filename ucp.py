#!/usr/bin/env python
from __future__ import print_function
import argparse
import os
import sys
try:
    import urllib.request as http  # python 3
except ImportError:
    import urllib as http  # python 2
import re
from collections import OrderedDict
from functools import reduce

cwd = os.path.dirname(sys.argv[0])
verbose = False
latest = 12
# upstream data
url_root_default = "https://www.unicode.org/Public/"
versions = OrderedDict(
    {"unicode-" + str(v): v for v in range(5, latest + 1)})
version_default = "unicode-" + str(latest)
versions_structure = {}
fns = {"u": "UnicodeData.txt", "d": "emoji-data.txt",
       "s": "emoji-sequences.txt", "z": "emoji-zwj-sequences.txt",
       "v": "emoji-variation-sequences.txt"}
parsers = {}
parsers["u"] = {
    "unicode-latest": [re.compile("^([^;]+);([^;]+).*$"), "cd"]}
parsers["d"] = {
    "unicode-6": [re.compile("^([^;]+[^ ])[ ]*;(?:[^;]+;){3}[^#]+#[^)]+\) (.*)$"), "cd"],
    "unicode-latest": [re.compile("^([^ ]+)[^#]+#[^[]+\[([0-9]+)\].*[ ]{2,}(.+)$"), "cnd"]}
parsers["s"] = {
    "unicode-latest": [re.compile("^([^;]+[^ ])[ ]*;[^;]+;[ ]*([^#]+[^ ])[ ]*#[^[]+\[([0-9]+)\].*$"), "cdn"]}
parsers["z"] = {
    "unicode-latest": parsers['s']['unicode-latest'] }
parsers["v"] = {
    "unicode-latest": parsers['s']['unicode-latest'] }

map_expressions_builtin = {
   '_emoji_': [0, re.compile('^0x1f[3-6][0-9a-f]{2}$')],
   '_emoji2_': [2, re.compile('^1$')]
}
map_expressions_negative = []
map_expressions_positive = []


def build_targets(root, remote=True):
    sep = "/" if remote else os.sep
    for n, v in versions.items():
        versions_structure[n] = {n: []}
        sub_path = str(v) + ".0.0/ucd" if remote else "upstream"
        versions_structure[n][n] = [
            ['u', sep.join([x.strip(sep) for x in \
                      [root, sub_path, fns['u']]])]]
    for uv, v, fs in zip(list(range(6, latest + 1)),
                         list(range(1, 6)) + list(range(11, latest + 1)),
                         ["d", *(["dsz"] * 3), *(["dszv"] * 3)]):
        nuv = "unicode-" + str(uv)
        nv = "emoji-" + str(v)
        versions_structure[nuv][nv] = []
        sub_path = "emoji/" + str(v) + ".0/" if remote else "upstream"
        for f in list(fs):
            versions_structure[nuv][nv].append(
                [f, sep.join([x.strip(sep) for x in \
                        [root, sub_path, fns[f]]])])


def parse_matchsets(matchsets):
    matchsets = matchsets.split(',')
    for m in matchsets:
        m = m.strip()
        if verbose:
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


def generate(source, version):
    print("# generating codepoints map", file=sys.stderr)
    if verbose:
        print("src: %r" % ("[stdin]" if source == '-' else source),
              file=sys.stderr)

    mappings = {}
    if os.path.isdir(source):
        # parse sources
        build_targets(source, False)

        nuv = version
        for [t, fp] in reduce(lambda l1, l2: l1 + l2,
                              versions_structure[nuv].values()):
            lines = []
            with open(fp, 'r') as f:
                lines = f.readlines()
            if verbose:
                print("processing %d lines of %r using parser type %r"
                      % (len(lines), fp, t), file=sys.stderr)
            for line in [line.strip()
                         for line in lines]:
                # skip blanks and comments
                if len(line) == 0 or line[0:1] == "#":
                    continue

                # parse with parser
                p = parsers[t][nuv] if nuv in parsers[t] \
                                    else parsers[t]["unicode-latest"]
                rx, bits = p[0], list(p[1])
                m = rx.match(line)
                if not m:
                    continue
                c = m.groups()[bits.index('c')]
                d = m.groups()[bits.index('d')]
                n = 1
                if 'n' in bits:
                    n = int(m.groups()[bits.index('n')])

                # cleanup
                description = d.lower().replace(' ', '-')
                if ' ' in c:
                    codepoint = ' '.join(hex(int(x, 16))
                                           for x in c.split(' '))
                else:
                    codepoint = hex(int(c.split('.')[0], 16))
                # insert mapping(s)
                if n == 1:
                    mappings[codepoint] = \
                       [description, 0 if t == 'u' else 1]
                else:
                    ci = int(codepoint, 16)
                    for l in range(n):
                        codepoint2 = hex(ci + l)
                        description2 = mappings[codepoint2][0] \
                            if codepoint2 in mappings \
                            else description + " " + str(l)
                        mappings[codepoint2] = [description2, 1]

        # dump mappings
        mappings = ["{0};{1};{2}".format(k, *v)
                    for k, v in mappings.items()]
        target = os.path.join(source, version + ".raw")
        f = None
        try:
            f = open(target, 'w')
            f.write('\n'.join(mappings))
        except Exception:
            print("cannot write to target file: %r" % (target),
                  file=sys.stderr)
            f.close()
            exit(1)

    else:
        # read map file
        with open(source, 'r') as f:
            mappings = f.readlines()
        source = os.path.dirname(source)

    if verbose:
        print("filtering %d codepoints" % (len(mappings)),
              file=sys.stderr)

    # build matches
    matches = []
    for parts in [line.split(';') for line in mappings]:
        match = 0
        for _, match_on, rx in map_expressions_negative:
            if rx.match(parts[match_on]):
                match = 1
                break
        if match == 1:
            continue  # negative match
        for _, match_on, rx in map_expressions_positive:
            if rx.match(parts[match_on]):
                match = 1
                break
        if match == 1:
            matches.append(";".join(parts[0:2]))

    print("mapped %d codepoints" % (len(matches)), file=sys.stderr)

    # write map file
    target = os.path.join(source, version + ".map")
    f = None
    try:
        f = open(target, 'w')
        f.write('\n'.join(matches))
    except Exception:
        print("cannot write to target file: %r" % (target),
              file=sys.stderr)
        f.close()
        exit(1)


def download(source, version, target):
    print("# downloading ICU codepoints for %r" % (version),
          file=sys.stderr)

    target = os.path.join(target, "upstream")
    if not os.path.isdir(target):
        try:
            os.makedirs(target)
        except Exception:
            print("cannot create target directory: %r" % (target),
                  file=sys.stderr)
            exit(1)

    build_targets(source)
    nuv = version
    for [t, url] in reduce(lambda l1, l2: l1 + l2,
                           versions_structure[nuv].values()):
        dest = os.path.join(target, fns[t])
        if verbose:
            print("src: %r" % (url), file=sys.stderr)
            print("dest: %r" % (dest), file=sys.stderr)

        f = None
        try:
            f = open(dest, 'w')
            f.close()
        except Exception:
            print("cannot write to target file: %r" % (dest),
                  file=sys.stderr)
            exit(1)
        try:
            http.urlretrieve(url, dest)
        except Exception as e:
            print("download failed:\n\n%s" % (e), file=sys.stderr)
            sys.exit(1)


parser = argparse.ArgumentParser(
    argument_default='-h',
    description='Unicode Codepoints Parser')
parser.add_argument(
    '-t', '--target', dest='target',
    type=str, nargs='?', default=version_default,
    help="unicode version to target")
parser.add_argument(
    '-lt', '--list-targets', action='store_const',
    const=True, default=False,
    help="list unicode versions available for targeting")
parser.add_argument(
    '-g', '--generate', action='store_const',
    const=True, default=False,
    help="generate the codepoints map")
parser.add_argument(
    '-d', '--download', action='store_const',
    const=True, default=False,
    help="download latest ICU codepoints data blob")
parser.add_argument(
    '-u', '--url', dest='url_root', nargs='?',
    default=url_root_default,
    help="set URL for ICU codepoints data blob")
parser.add_argument(
    '-ms', '--matchsets', dest='matchsets',
    default='_emoji2_',
    help="comma delimited list of pre-defined matchsets" +
         " and/or arbitrary match strings")
parser.add_argument(
    '-s', '--source', type=str, default='-',
    help="ICU codepoints data blob (default: stdin)")
parser.add_argument(
    '-v', '--verbose', action='store_const',
    const=True, default=False,
    help="increase the level of information output")

if not sys.argv[1:]:
    parser.print_help(sys.stderr)
    exit(0)

args = parser.parse_args()

source = args.source
version = args.target
verbose = args.verbose
if args.download:
    target = os.path.join(cwd, 'codepoints', version)
    download(args.url_root, version, target)
    source = target
if args.generate:
    try:
        parse_matchsets(args.matchsets)
    except Exception as e:
        print("error: %s" % (e), file=sys.stderr)
        exit(1)
    sys.argv = [sys.argv[0]]
    generate(source, version)
if args.list_targets:
    build_targets(args.url_root)
    for nv in versions.keys():
        print("version: '%s'" % (nv), file=sys.stderr)
        if not verbose:
            continue
        for snv in versions_structure[nv]:
            print("  set: %s | %s" % (snv, versions_structure[nv][snv]),
                  file=sys.stderr)
