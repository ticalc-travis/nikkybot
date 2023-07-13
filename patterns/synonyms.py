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

from ._table import *

patterns = (
# Legal forms:
# pattern regexp, priority, action
# pattern regexp, priority, action, allow repeat?
# pattern regexp, last reply, priority, action, allow repeat?

# Synonyms
(r'\b(saxjax|tardmuffin|censor)', 98,
    R(
        Markov('saxjax'),
        Markov('tardmuffin'),
        Markov('censor'),
    ),
),
(r'\b(forum|moderator|admin)', 98,
    R(
        Markov('post'),
        Markov('forum'),
        Markov('moderator'),
        Markov('admin'),
        Markov('ban'),
    )
),
(r'\b(ping|pong)', 98,
    R(
        Markov('ping'),
        Markov('pong'),
    )
),
(r'\b(kerm|kermm|kerm martian|christopher)', 98,
    R(
        Markov('kerm'),
        Markov('kermm'),
        Markov('kerm martian'),
        Markov('christopher'),
        Markov('christopher mitchell'),
        Markov('repo'),
    )
),
(r'\b(djomni|dj.omni|dj.o|kevin_o)', 98,
    R(
        Markov('DJ_Omni'),
        Markov('DJ_O'),
        Markov('Kevin_O'),
    )
),
(r'\b(omnimaga|omnidrama)', 98,
    R(
        Markov('omnimaga'),
        Markov('omnidrama'),
    )
),
(r'\b(mudkip|herd|liek)', 98,
    R(
        Markov('mudkip'),
        Markov('mudkipz'),
        Markov('mudkips'),
        Markov('here u liek'),
        Markov('herd u liek'),
    ),
),
(r'\b(fire|bonfire|burn|flame|extinguish|fry|fries)', 1,
    R(
        Markov('fire'),
        Markov('fires'),
        Markov('fire alarm'),
        Markov('fire alarms'),
        Markov('bonfire'),
        Markov('bonfires'),
        Markov('burn'),
        Markov('burns'),
        Markov('flame'),
        Markov('flames'),
        Markov('extinguish'),
        Markov('extinguisher'),
        Markov('extinguishers'),
        Markov('fry'),
        Markov('fries'),
    )
),
(r'(\!q|\bquot).*', 1,
    R(
        Markov('!qadd'),
        Markov('!qfind'),
        Markov('!qdel'),
        Markov('quote'),
        Markov('quotes'),
        Markov('!qsay'),
    ),
),
(r'^[0-9]+ quotes? found:', -2,
    R(
        Markov('!qadd'),
        Markov('!qdel'),
        Markov('quote'),
        Markov('quotes'),
        Markov('!qsay'),
    ),
),
(r'(\bponie|\bpony|\bmlp\b)', 98,
    R(
        Markov('pony'),
        Markov('ponies'),
        Markov('poniez'),
        Markov('mlp'),
    ),
),
(r'(\bgov\b|\bgovernment|\bnsa\b|\bspy|\bspies\b|\bdrone)', 98,
    R(
        Markov('nsa'),
        Markov('spy'),
        Markov('spies'),
        Markov('drones'),
    ),
),
(r'(\bpokemon|\bpokémon|\bmudkip|pokedex)', 98,
    R(
        Markov('pokemon'),
        Markov('mudkip'),
        Markov('mudkips'),
        Markov('mudkipz'),
    ),
),
(r'\b(ut|ut2004|ututut)\b', 98,
    R(
        Markov('ut'),
    ),
),
(r'\b(highlight|hilight)', 98,
    R(
        Markov('highlight'),
        Markov('hilight'),
    ),
),
(r'\b(program|code)', 98,
    R(
        Markov('program'),
        Markov('code'),
        Markov('programming'),
        Markov('coding'),
    ),
),
(r'\b(git|mercurial|svn|cvs|commit|merge)', 0,
    R(
        Markov('git'),
        Markov('mercurial'),
        Markov('svn'),
        Markov('cvs'),
        Markov('commit'),
        Markov('merge'),
    ),
),
(r'\b(news|cnn|fox|cbs)', 0,
    R(
        Markov('news outlet'),
        Markov('cnn'),
        Markov('fox'),
        Markov('cbs'),
    ),
),
(r'\b(browser|firefox|opera|mosaic|netscape|chrome|chromium)', 0,
    R(
        Markov('browser'),
        Markov('firefox'),
        Markov('opera'),
        Markov('mosaic'),
        Markov('netscape'),
        Markov('chrome'),
        Markov('chromium'),
    ),
),
(r'\b(irc client|weechat|irssi|\w*chat|kiwiirc|web client|webchat|web chat|mirc|bitchx|sax)', 0,
    R(
        Markov('irc client'),
        Markov('bitchx'),
        Markov('irssi'),
        Markov('weechat'),
        Markov('mirc'),
    ),
),
(r'\b(os|windows|mac|linux|unix)\b', 0,
    R(
        Markov('os'),
        Markov('windows'),
        Markov('mac'),
        Markov('linux'),
        Markov('unix'),
    ),
),
(r'\b(speak|talk|words)', 98,
    R(
        Markov('speak'),
        Markov('talk'),
        Markov('words'),
        Markov('speaking'),
        Markov('talking'),
    ),
),

# Transformations
(r'(.*)\bI am\b(.*)', 99, Markov('{1} you are {2}')),
(r'(.*)\byou are\b(.*)', 99, Markov('{1} I am {2}')),
(r'(.*)\bme\b(.*)', 0, Markov('{1} you {2}')),

)
