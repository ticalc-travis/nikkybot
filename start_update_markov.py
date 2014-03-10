#!/usr/bin/env python2

import sys
import update_markov
from personalitiesrc import personality_regexes

reset = False
try:
    if sys.argv[1] == 'RESET':
        reset = True
except IndexError:
    pass

for p in sorted(personality_regexes.keys()):
    update_markov.update(p, reset)

