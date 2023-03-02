# -*- coding: utf-8 -*-

# “NikkyBot”
# Copyright ©2012-2016 Travis Evans
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


def random_number(nikkyai, context, fmt):
    from random import randint
    c = randint(0, 3)
    if c == 0:
        out = str(randint(0,9999))
    elif c == 1:
        out = str(randint(0,999999999999))
    else:
        out = '{}\nLong enough for you?'.format(randint(0, int('9'*100)))
    return out


def mimic(nikkyai, context, fmt):
    from nikkyai import Bad_personality_error
    src_nick, persona, msg = fmt[0], fmt[2], fmt[3]
    persona = nikkyai.normalize_personality(persona)
    try:
        nikkyai.set_personality(persona)
    except Bad_personality_error:
        out = "Sorry, no personality named '{}' yet. {}".format(
            persona, nikkyai.get_personalities_text())
    else:
        in_msg = '<{}> {}'.format(src_nick, msg)
        out = ('"' + nikkyai.reply(
            in_msg, context=context, add_response=True) + '"')
    finally:
        nikkyai.set_personality('nikky')
    return out


def mimic_random(nikkyai, context, fmt):
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
            persona, nikkyai.reply(in_msg, context=context, add_response=True))
    finally:
        nikkyai.set_personality('nikky')
    return out


def mimic_speaker(nikkyai, context, fmt):
    src_nick = fmt[0]
    new_fmt = (src_nick, None, src_nick, fmt[3])
    return mimic(nikkyai, context, new_fmt)


def list_personas(nikkyai, context, fmt):
    return nikkyai.get_personalities_text()


patterns = (
# Legal forms:
# pattern regexp, priority, action
# pattern regexp, priority, action, allow repeat?
# pattern regexp, last reply, priority, action, allow repeat?

# Help
(r"(^\W*help|(what'?s|who'?s|what is|who is|what are|who are|wtf is|wtf are) (a |an |the )?(you|{0})\??$|(what'?s|what does) (you|{0}) do(\W|$))", -99,
    S("I'm a Markov-chain bot representing Nikky. https://raw.githubusercontent.com/ticalc-travis/nikkybot/master/README"),
True),

# Random number
(r'\brandom number\b', -2, E(random_number)),

(r'\bfun *fact', -10, Markov_forward('fun fact', order=3)),

# Mimic
(r'^\W*(mimic|impersonate|act like|imitate)\s*$', -98, E(mimic_random), True),
(r'^\W*(mimic|impersonate|act like|imitate)\W+(\S+)(?: |$)(.*)', -98, E(mimic), True),
(r'^\W*(mimic|impersonate|act like|imitate)\W+(someone|anyone|somebody|anybody|random|rand)(?: |$)(.*)', -99, E(mimic_random), True),
(r'^\W*(mimic|impersonate|act like|imitate)\W+(me|myself)(?: |$)(.*)', -99, E(mimic_speaker), True),
(r'^\W*(personas|personalities)\b', -99, E(list_personas), True),

# Markov
(r'^!say', -99, '%echo !say HAW HAW INFINITE LOOP', True),
)
