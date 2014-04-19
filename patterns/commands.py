# -*- coding: utf-8 -*-

# “NikkyBot”
# Copyright ©2012-2014 Travis Evans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from _table import *


def random_nikkysim(nikkyai, fmt):
    return nikkyai.nikkysim(strip_number=False)[0]


def nikkysim_no(nikkyai, fmt):
    w, x, y = fmt[1], fmt[2], fmt[3]
    if w == None:
        w = 'B-'
    if y == None:
        y = '-0'
    x, y = int(x), int(y.strip('-'))
    if w == 'A-' or w == 'a-':
        return "Only tev's TI-89 NikkySim can do the 'A-' quotes"
    elif w == 'B-' or w == 'b-' or w is None:
        if (x >= 0 and x <= 4294967295) and (y >= 0 and y <= 9999):
            return nikkyai.nikkysim(False, (x, y))[0]
        else:
            return 'Sayings go from 0-0 to 4294967295-9999, champ'
    else:
        return "No such thing as a {}type quote yet".format(w)


def tell_us_something(nikkyai, fmt):
    pre = choice(
        ["","","","","","Okay\\n","k\\n","kk\\n","Fine\\n"])
    return pre + nikkyai.nikkysim(strip_number=True)[0]


def random_number(nikkyai, fmt):
    from random import randint
    c = randint(0, 3)
    if c == 0:
        out = str(randint(0,9999))
    elif c == 1:
        out = str(randint(0,999999999999))
    else:
        out = '{}\nLong enough for you?'.format(randint(0, int('9'*100)))
    return out


def mimic(nikkyai, fmt):
    from nikkyai import Bad_personality_error
    persona, msg = fmt[2], fmt[3]
    try:
        nikkyai.set_personality(persona)
    except Bad_personality_error:
        out = "No such personality '{}'; say \"{}: ?personalities\" to get the list".format(persona, nikkyai.nick)
    else:
        out = '"' + nikkyai.reply(msg, add_response=True) + '"'
    finally:
        nikkyai.set_personality('nikky')
    return out


patterns = (
# Legal forms:
# pattern regexp, priority, action
# pattern regexp, priority, action, allow repeat?
# pattern regexp, last reply, priority, action, allow repeat?

(r'\b(random (quote|saying)|nikkysim)\b', -2,
    E(random_nikkysim)
),
(r'\b(tell|tell us|tell me|say) (something|anything) (.*)(smart|intelligent|funny|interesting|cool|awesome|bright|thoughtful|entertaining|amusing|exciting|confusing|sensical|inspiring|inspirational|random|wise)\b', 1,
    E(tell_us_something)
),
(r'(?<![0-9])#([A-Za-z]-)?([0-9]+)(-([0-9]+))?', -2, E(nikkysim_no), True),
(r'\brandom number\b', -2, E(random_number)),
(r'^(mimic|impersonate|act like|imitate) (\S+) ?(.*)', -99, E(mimic), True),
(r'\b(markovmix|markov bot)', -99,
    R('I can impersonate people\nSay "?personalities" to me and I\'ll tell you more'),
),
(r'^\??markov5 (.*)', -99, Manual_markov(5, '{1}'), True),
(r'^\??markov4 (.*)', -99, Manual_markov(4, '{1}'), True),
(r'^\??markov3 (.*)', -99, Manual_markov(3, '{1}'), True),
(r'^\??markov2 (.*)', -99, Manual_markov(2, '{1}'), True),
(r'^\??markov5nr (.*)', -99, Manual_markov(5, '{1}'), False),
(r'^\??markov4nr (.*)', -99, Manual_markov(4, '{1}'), False),
(r'^\??markov3nr (.*)', -99, Manual_markov(3, '{1}'), False),
(r'^\??markov2nr (.*)', -99, Manual_markov(2, '{1}'), False),
(r'^\??markov5f (.*)', -99, Manual_markov_forward(5, '{1}'), True),
(r'^\??markov4f (.*)', -99, Manual_markov_forward(4, '{1}'), True),
(r'^\??markov3f (.*)', -99, Manual_markov_forward(3, '{1}'), True),
(r'^\??markov2f (.*)', -99, Manual_markov_forward(2, '{1}'), True),
(r'^\??markov5fnr (.*)', -99, Manual_markov_forward(5, '{1}'), False),
(r'^\??markov4fnr (.*)', -99, Manual_markov_forward(4, '{1}'), False),
(r'^\??markov3fnr (.*)', -99, Manual_markov_forward(3, '{1}'), False),
(r'^\??markov2fnr (.*)', -99, Manual_markov_forward(2, '{1}'), False),

)
