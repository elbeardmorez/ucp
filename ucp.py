#!/usr/bin/env python
import fileinput
import re

emoticon_match = re.compile('^1F[3456][0-9ABCDEF]{2}')


for line in fileinput.input():
    if emoticon_match.match(line) :
        (cp,desc) = line.split(';')[0:2]
        desc = desc.lower().replace(' ','-')
        cp = cp.lower()
        print('\t"{0}" : 0x{1},'.format(desc,cp))
