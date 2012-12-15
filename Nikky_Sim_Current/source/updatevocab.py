#!/usr/bin/env python3

from os import listdir

names = sorted([fn for fn in listdir('vocabulary') if fn.endswith('.txt')])

csrc = open('words.inc', 'w')

for n in names:
        csrc.write('\nVOCAB_TABLE(' + n[:-4] + ')\n')
        with open('vocabulary/' + n, 'r') as f:
                for l in f.readlines():
                        l = l.strip()
                        p, w = l[:l.find(' ')], l[l.find(' ')+1:]
                        w = w.replace('"', '\\"')
                        if "\\xE9" in w:
                            csrc.write(
                                '#ifdef CLI_PC_BUILD\n'
                                '    ENTRY("%s", 0, %s)\n'
                                '#else\n'
                                '    ENTRY("%s", 0, %s)\n'
                                '#endif\n' % (w.replace("\\xE9", "é"), p, w, p))
                        else:
                            csrc.write('     ENTRY("%s", 0, %s)\n' % (w, p))
                csrc.write('TABLE_END\n')

csrc.close()
