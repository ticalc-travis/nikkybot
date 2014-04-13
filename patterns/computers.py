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

patterns = (
# Legal forms:
# pattern regexp, priority, action
# pattern regexp, priority, action, allow repeat?
# pattern regexp, last reply, priority, action, allow repeat?

# General
(r'\b(what command|which command|what (command )?do .* enter|what (command )?should .* enter|what (command )?do .* type|what (command )?should .* type)\b', 0,
    R(
        Markov_forward('sudo'),
        Markov_forward('chown'),
        Markov_forward('rm'),
        Markov_forward('su'),
        Markov_forward('format c:'),
        Markov_forward('/quit'),
        Markov_forward('!list')
    )
),
(r'\b(sudo )?rm \-?rf\b', 1, R('\001ACTION deletes himself\001')),
(r'\bzombie', 1,
    R(
        "Don't use shitnix",
        "Don't use Linux. Problem solved.",
        Recurse('what do you think of linux'),
        Recurse('what do you think of unix')
    )
),
(r'[0-9][0-9](\"|inch|\-inch) (3d |3-d )?(lcd|monitor|plasma|crt|dlp)', 1,
    R(
        Markov_forward('big monitors'),
        Markov('monitors'),
    ),
),
(r'\b(monitors|monitor-)', 1,
    R(
        'anyone with more than one monitor\nis a loser',
        Recurse('more than one monitor'),
        Markov_forward('big monitors'),
    )
),

# Programming
(r'\b(BASIC\b|C\+\+|C#|C\s\b|Java\b|Javascript\b|Lua\b|\s\.NET\s\b|Ruby\b|TCL\b|TI\-BASIC\b|TI BASIC\b|Python\b|PHP\b|Scheme\b)', 2,
    R(
        Markov_forward('{1}'),
        Markov_forward('{1} sucks'),
        'Perl is better',
        'Just use Perl',
        'Should have used Perl',
        'Perl was my first language',
        'Hahahaha\n{1}tard',
        'Hahahaha\nWhat a tard'
    )
),
(r'\b(which|what) language\b', 1, R('Perl\nDuh')),
(r'\b(which|what) site\b', 1,
    R('nvm2u.com', '{0}sucks.org', 'omnimaga.org', 'yourmom.org')
),
(r'\bi\b.*\buse(|d|ing)\b.*\bperl\b', 1,
    R('Good for you', '{0} is such a champ', Markov_forward('perl'))
),

)
