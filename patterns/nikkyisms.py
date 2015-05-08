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
import nikkyai

# Distinctive “Nikky-like” phrases

def more_like(nikkyai, context, fmt):
    src_nick = fmt[0]
    word = fmt[1].strip()
    if not word:
        out = nikkyai.markov_reply(
            '<{}> \nmore like'.format(src_nick), failmsg='', context=context,
            add_response=False, max_lf_l=2, max_lf_r=2)
    else:
        c = randint(0, 2)
        if not c:
            out = nikkyai.markov_forward(
                (word, '\n', 'more', 'like'), failmsg='', context=context,
                 src_nick=src_nick, max_lf=3)
        elif c == 1:
            out = nikkyai.markov_forward(
                (word, 'more', 'like'), failmsg='', context=context,
                 src_nick=src_nick, max_lf=3)
        elif c == 2:
            out = '{}\n{}'.format(
                word, nikkyai.markov_forward(
                    ('more', 'like'), failmsg='', context=context,
                     src_nick=src_nick, max_lf=1))
    return out


patterns = (
# Legal forms:
# pattern regexp, priority, action
# pattern regexp, priority, action, allow repeat?
# pattern regexp, last reply, priority, action, allow repeat?

(r'\b(diaf|fire)\b', 1,
    R(
        '\001ACTION burns\001',
        S(
            '\001ACTION lights himself on fire\001',
            R('','\n\001ACTION burns\001')
        ),
        'kk'
    )
),
(r'\breboot\b', 1,
    R(
        '\001ACTION reboots {0}\001\nlolrotflrebooted',
        'Or you can start using a halfway decent OS'
    )
),
(r'(.*?)\S*more like\S*$', -10, E(more_like)),
(r'\b(care|cares|careometer|care-o-meter)', -10,
    R(
        Markov_forward('* care-o-meter'),
        Markov_forward('* cares'),
    ),
),
)
