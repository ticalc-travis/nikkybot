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

# Special commands


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
    src_nick, persona, msg = fmt[0], fmt[2], fmt[3]
    persona = nikkyai.normalize_personality(persona)
    try:
        nikkyai.set_personality(persona)
    except Bad_personality_error:
        out = "No such personality '{}'; say \"{}: personalities\" to get the list".format(persona, nikkyai.nick)
    else:
        in_msg = '<{}> {}'.format(src_nick, msg)
        out = '"' + nikkyai.reply(in_msg, add_response=True) + '"'
    finally:
        nikkyai.set_personality('nikky')
    return out


def mimic_random(nikkyai, fmt):
    from random import choice
    from nikkyai import Bad_personality_error
    src_nick = fmt[0]
    try:
        msg = fmt[3]
    except IndexError:
        msg = ''
    persona = choice(nikkyai.get_personalities())
    try:
        nikkyai.set_personality(persona)
    except:
        raise
    else:
        in_msg = '<{}> {}'.format(src_nick, msg)
        out = '<{}> {}'.format(
            persona, nikkyai.reply(in_msg, add_response=True))
    finally:
        nikkyai.set_personality('nikky')
    return out


def list_personas(nikkyai, fmt):
    personas = [nikkyai.munge_word(p) for p in nikkyai.get_personalities()]
    return ('List of personalities: \n{}\n'
            'Say "{}: mimic <personality> <message>" to "talk" to that '
            'personality.\n'
            'Talk to tev to request a new personality based on '
            'someone.\n'.format(', '.join(sorted(personas)), nikkyai.nick))


patterns = (
# Legal forms:
# pattern regexp, priority, action
# pattern regexp, priority, action, allow repeat?
# pattern regexp, last reply, priority, action, allow repeat?

# Help
(r'^\W*help', -99,
    S('Basic info about me: https://raw.githubusercontent.com/ticalc-travis/nikkybot/master/README'),
True),

# NikkySim
(r'\b(random (quote|saying)|nikkysim)\b', -2,
    E(random_nikkysim)
),
(r'(?<![0-9])#([A-Za-z]-)?([0-9]+)(-([0-9]+))?', -2, E(nikkysim_no), True),

# Random number
(r'\brandom number\b', -2, E(random_number)),

# Misc
(r'\b(tell|tell us|tell me|say) (something|anything) (.*)(smart|intelligent|funny|interesting|cool|awesome|bright|thoughtful|entertaining|amusing|exciting|confusing|sensical|inspiring|inspirational|random|wise)\b', 1,
    E(tell_us_something)
),

# Mimic
(r'^\W*(mimic|impersonate|act like|imitate)\s*$', -98, E(mimic_random), True),
(r'^\W*(mimic|impersonate|act like|imitate)\W+(\S+)(?: |$)(.*)', -98, E(mimic), True),
(r'^\W*(mimic|impersonate|act like|imitate)\W+(someone|anyone|somebody|anybody|random|rand)(?: |$)(.*)', -99, E(mimic_random), True),
(r'\b(markovmix|markov bot)', -99,
    R('I can impersonate people\nSay "?personalities" to me and I\'ll tell you more'),
),
(r'^\W*(personas|personalities)\b', -99, E(list_personas), True),

# Markov
(r'^!say', -99, '%echo !say HAW HAW INFINITE LOOP', True),
)
