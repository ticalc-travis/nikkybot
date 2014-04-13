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


def more_like(nikkyai, fmt):
    # !TODO! Now that it's a function, we can improve this now!
    return nikkyai.markov_reply("\n more like \n", add_response=False)


patterns = (
# Legal forms:
# pattern regexp, priority, action
# pattern regexp, priority, action, allow repeat?
# pattern regexp, last reply, priority, action, allow repeat?

# Basics
(r"\b(hi|hello|hey|sup|what's up|welcome)\b", 0,
    R(
        Markov_forward('{1}'),
        Markov_forward('{1} {0}'),
        '{1}, {0}',
        'Shut up',
        'Flood your face!',
        'FLOOD YOUR FACE',
        'Go away',
        'No\ngo away',
        Markov_forward('shut the'),
        Markov_forward('I heard {0}'),
        Markov_forward('I heard that {0}'),
    ),
),
(r"\b(how are you|how are we|how's your|how is your)\b", 0,
    R('Super', 'Awesome', 'Better than your face',
        Markov_forward('better than'),
        Markov_forward('better than your'),
        Markov_forward('worse than'),
        Markov_forward('worse than your')
    ),
),
(r"\b(good night|goodnight|g'?night)\b", 0,
    R(
        Markov_forward('night'),
        Markov_forward('night {0}'),
        Markov_forward('sweet dreams')
    )
),
(r"\b(bye|bye bye|goodbye|good bye|see you later|night|good night|g'night)\b",
0,
    R(
        'Bye forever',
        'I hope I never see you again',
        'BYE FOREVER',
        'I HOPE I NEVER SEE YOU AGAIN',
        'Loser',
        "Loser\nWe don't need you anyway",
        'bye lamers',
        'Good riddance',
        Markov_forward('bye'),
        Markov_forward('bye {0}')
    ),
),
(r"\b(congratulations|congrats|congradulations)", 1, R('Thanks', 'thx')),
(r'\b(brb|be right back)\b', 1, R('k', 'kk')),
(r'\b(thanks|thank you)\b', 1,
    R(
        Markov_forward("you're welcome"),
        'np'
    )
),
(r'\bno\W*thanks\b', 1, R('DIAF then')),
(r'\b(wb|welcome back|welcoem back)\b', 1, R('Thanks', 'No\nGo away')),
(r"\*\*\*yes/no\*\*\*", -99,
    R(
        Markov_forward('yes'),
        Markov_forward('no'),
        Markov_forward('maybe'),
        Markov_forward('yeah'),
        Markov_forward('probably'),
        Markov_forward('yes'),
        Markov_forward('only if'),
        Markov_forward('only when'),
        Markov_forward('as long as'),
        Markov_forward('whenever'),
        Markov_forward('of course')
    )
),

# General
(r"which", 1,
    R(
        Markov_forward('this'),
        Markov_forward('that'),
        Markov_forward('the'),
        Markov_forward('those'),
        Markov_forward('these'),
        Markov_forward('all of'),
        Markov_forward('all the'),
    ),
),
(r"^anything else", 1,
    S(
        R('', Recurse('***yes/no***')),
        '\n',
        Recurse("what's"),
    ),
),
(r"^(what do you|what is going|what's going)", -2, Recurse('for what')),
(r"(^(what|what's|whats)|for what|for which)", 1,
    R(
        Markov_forward('a'),
        Markov_forward('an'),
        Markov_forward('the'),
        Markov_forward("It's a"),
        Markov_forward("It's an"),
        Markov_forward("It's the"),
        Markov_forward("It is a"),
        Markov_forward("It is an"),
        Markov_forward("It is the"),
        Recurse('how many'),
    ),
),
(r"^(who is|who's|what is|what's|how's|how is) (the |a |an |your |my )?(.*?)\?*$", 0,
    R(
        Markov_forward('{3} is'),
        Markov_forward('{3}'),
        Markov_forward('A {3} is'),
        Markov_forward('An {3} is'),
        Markov_forward('The {3} is'),
        Markov_forward('A {3}'),
        Markov_forward('An {3}'),
        Markov_forward('The {3}'),
        Recurse("what's"),
    ),
),
(r"^(who are|who're|what are|what're|how're|how are) (.*?)\?*$", 0,
    R(
        Markov_forward('{2} are'),
        Markov_forward("They're"),
        Markov_forward('They are'),
    ),
),
(r"^(what are|what're) .*ing\b", -1,
    Recurse("what's"),
),
(r'^where\b', 0,
    R(
        Markov_forward('in'),
        Markov_forward('on'),
        Markov_forward('on top of'),
        Markov_forward('inside of'),
        Markov_forward('inside'),
        Markov_forward('under'),
        Markov_forward('behind'),
        Markov_forward('outside'),
        Markov_forward('over'),
        Markov_forward('up'),
        Markov_forward('beyond'),
    )
),
(r'^when\b', 1,
    R(
        'never',
        'forever',
        'right now',
        'tomorrow',
        'now',
        Markov_forward('never'),
        Markov_forward('tomorrow'),
        Markov_forward('as soon as'),
        Markov_forward('whenever'),
        Markov_forward('after'),
        Markov_forward('before'),
        Markov_forward('yesterday'),
        Markov_forward('last'),
        Markov_forward('next'),
    )
),
(r'^how (long|much longer|much more time)\b', -2,
    R(
        'never',
        'forever',
        Markov_forward('until'),
        Markov_forward('as soon as'),
        Markov_forward('whenever'),
    )
),
(r'^how\b', -1,
    R(
        Markov_forward('by'),
        Markov_forward('via'),
        Markov_forward('using'),
        Markov_forward('use'),
        Markov_forward('only by'),
        Markov_forward('only by using'),
        Markov_forward('just use'),
    )
),
(r'\b(you suck|your .* sucks)\b', 1,
    R(
        ':(',
        'Die',
        'DIAF',
        'STFU',
        'Suck it',
        'Suck it dry',
        ':(\nDo I suck?',
        Markov_forward('So does')
    )
),
(r'\bsuck (a |an )\b(.*)\b', 1,
    R('k', 'kk', 'kk\n\001ACTION sucks {1}{2}\001')
),
(r'\bShut up\b', 1, R('I hate you', 'k', 'kk', 'nou', 'NO U', 'NOU')),
(r"\bI'm\b", 1,
    R(
        'Congratulations',
        'Uh, congratulations?',
        'k',
        'nice',
        "I'm sorry",
        Recurse("you're")
    )
),
(r'\bdiaf\b', 1,
    R(
        '\001ACTION burns\001',
        S(
            '\001ACTION lights himself on fire\001',
            R('','\n\001ACTION burns\001')
        ),
        'kk'
    )
),
(r"\b(would you like|want to|you want to|wanna|you wanna) (see|hear|read)\b", 1,
    R("Yes, please bore us to death.")
),
(r'\bwho am i\b', -1, R('You are {0}', Markov_forward('you are'))),
(r'\bwho (are you|is nikkybot)\b', -1,
    R(
        Markov_forward("I'm"),
        Markov_forward("I am"),
    ),
),
(r'\breboot\b', 1,
    R(
        '\001ACTION reboots {0}\001\nlolrotflrebooted',
        'Or you can start using a halfway decent OS'
    )
),
(r'\bwhere.*you hear that\b', 1, R('Omnimaga', 'your mom', 'your face')),
(r'\b(why|how come)\b', 0,
    R(
        Markov_forward('because'),
        Markov_forward('because your'),
        Markov_forward('because you'),
        Markov_forward('because of'),
        Markov_forward('because of your')
    )
),
(r'\b(lousy|freaking|stupid|damn|dumb|farking|dammit|damnit|screw)\b', 1,
    S(
        R(
            'sorry\n',
            'sry\n',
            'sorry\n:(\n',
        ),
        Recurse('excuse me while I'),
    )
),
(r'\b((are|is) \S+|you) t?here\b', 0,
    R(
        'no',
        "No\nhe said he's never talking to anyone again",
        'no\ngo away',
        'Shut up'
    )
),
(r'\b(oops|oops|whoops|oopsie|oppsie)\b', 1, R('HAHAHAHAHA\nFAIL')),
(r'\bi hate\b', 1,
    R(
        "Don't use it",
        "Don't use it\nProblem solved!",
        'me too',
        'I hate it too',
        "Don't use it\nI hate it too"
        'I hate you too',
        ':(\nI hate you too',
        'I HATE YOU {0}\nNerd',
        Markov_forward('I hate'),
    )
),
(r'\bwhat does it mean\b', 1,
    R('Communism.', Markov_forward('it means'))
),
(r'\b(who|what) (does|do|did|should|will|is) (\S+) (.*?)\?*$', -1,
    R(
        Recurse('which'),
        Markov_forward('{3} {4}'),
        Markov_forward('{3} {4}s'),
    ),
),
(r'\bcontest\b', 1,
    R(
        Recurse("I'm entering"),
        Recurse("You'll lose"),
        Recurse('My entry'),
        Markov_forward('Contests'),
        Markov('contest')
    )
),
(r'\b(fever|cold|sick|ill|vomit|throw up|mucus|infection|injury|under the weather|a cold|flu)\b', 1,
    R('I HOPE YOU STAY SICK FOREVER', 'Will a hug make it better?')
),
(r'\bfault\b', 1,
    R(
        Markov_forward("It's your fault"),
        S("No, it's your ", R("mom's", "face's"), " fault")
    )
),
(r"\bi don't feel like\b", 1,
    R(
        'lazy',
        'slacker',
        "I don't feel like reading what you write",
        'me neither',
        ':(',
        'DO IT ANYWAY'
    )
),
(r'\brules\b', 1, R("\001ACTION rules {0}\001")),
(r'\b(how much|how many|what amount)\b', -2,
    R(
        Markov_forward('enough'),
        Markov_forward('too many'),
        Markov_forward('more than you'),
        Markov_forward('not enough'),
    )
),
(r'\bnikkybot.*more like\W*$', -20,
    R(
        'nikkybot\nmore like\nchamp',
        "nikkybot\nmore like\nI'm always the best",
        'nikkybot\nmore like\nawesome',
    ), True
),
(r'\bmore like\W*$', -10, E(more_like)),
(r'(.*) (more|moer|mroe) (like|liek)\W*$', -15,
    R(
        Markov_forward('{1} \n more like'),
        S(
            '{1}\n',
            Markov_forward('more like \n', max_lf_r=2)
        ),
    ),
),
(r"^(is|isn't|are|am|does|should|can|do)\b", 2, Recurse('***yes/no***')),
(r'^(do you think|what about|really)\b', 0, R(Recurse('***yes/no***'))),
(r"^(is|are|am|should|can|do|does|which|what|what's|who|who's)(?: \S+)+[ -](.*?)\W+or (.*)\b", -1,
    S(
        R(
            S('{2}', R(' by far', ', of course', ', naturally', '\nduh')),
            S('{3}', R(' by far', ', of course', ', naturally', '\nduh')),
            'both',
            'neither',
            'dunno',
            S('{2}', R('--', '? ', ': ', '\n'), Recurse('what do you think of {2}')),
            S('{3}', R('--', '? ', ': ', '\n'), Recurse('what do you think of {3}'))
        ),
        '\n',
        R('', Markov_forward('because', [' ']), Markov_forward('since', [' '])),
    ),
),
(r'\bwhat time\b', 0,
    R(
        Markov_forward('time for'),
        Markov_forward("it's time"),
    ),
),
(r"\b(will|should|can|going to|won't|wouldn't|would|can't|isn't|won't) (\w+)\b", 5,
    R(
        Markov_forward('and'),
        Markov_forward('and just'),
        Markov_forward('and then'),
        Markov_forward('and then just'),
        Markov_forward('or'),
        Markov_forward('or just'),
        Markov_forward('yes and'),
        Markov_forward('yes or'),
        Markov_forward('yeah and'),
        Markov_forward('yes and'),
        Markov_forward('yes and just'),
        Markov_forward('yes or just'),
        Markov_forward('yeah and just'),
        Markov_forward('yes and just'),
        Markov_forward('and {2}'),
        Markov_forward('and just {2}'),
        Markov_forward('and then {2}'),
        Markov_forward('and then just {2}'),
        Markov_forward('or {2}'),
        Markov_forward('or just {2}'),
        Markov_forward('yes and {2}'),
        Markov_forward('yes or {2}'),
        Markov_forward('yeah and {2}'),
        Markov_forward('yes and {2}'),
        Markov_forward('yes and just {2}'),
        Markov_forward('yes or just {2}'),
        Markov_forward('yeah and just {2}'),
        Markov_forward('yes and just {2}'),
        Markov_forward('why'),
    ),
),
(r"(?:\bi|')s\b.*\b(a|an) (.*)", -5,
    S(
        R('{0}', "{0}'s mom", "{0}'s face", 'your mom', 'your face'),
        R(' ', '\n'),
        'is {1} {2}',
    ),
),

)
