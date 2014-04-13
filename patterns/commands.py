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

(r'\b(random (quote|saying)|nikkysim)\b', -2,
    E('nikkysim(strip_number=False)[0]')
),
(r'\b(tell|tell us|tell me|say) (something|anything) (.*)(smart|intelligent|funny|interesting|cool|awesome|bright|thoughtful|entertaining|amusing|exciting|confusing|sensical|inspiring|inspirational|random|wise)\b', 1,
    E('choice(["","","","","","Okay\\n","k\\n","kk\\n","Fine\\n"])+nikkysim(strip_number=True)[0]')
),
(r'(?<![0-9])#([A-Za-z]-)?([0-9]+)(-([0-9]+))?', -2,
    E('nikkysim_parse_saying_no("{1}", "{2}", "{3}")'),
    True
),
(r'\brandom number\b', -2,
    R(
        E('randint(0,9999)'),
        E('randint(0,999999999999)'),
        E('str(randint(0,int(\'9\'*100))) + "\\nLong enough for you?"')
    ),
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
