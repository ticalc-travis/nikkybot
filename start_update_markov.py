#!/usr/bin/env python2

import update_markov
from personalitiesrc import personality_regexes

for p in personality_regexes.keys():
    for o in (2, 3, 4, 5):
        update_markov.update(p, o, False)

