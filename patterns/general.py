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

# General patterns for 'nikky' personality

def more_like(nikkyai, fmt):
    # !TODO! Implement our own looping; fail to default 'more like' completion
    # Need a way to access RECURSE_LIMIT from here first (make it an attribute
    # of NikkyAI)
    if not fmt[1]:
        return nikkyai.markov_reply('\n more like \n', add_response=False)
    out = nikkyai.markov_forward((fmt[1], '\n', 'more', 'like'),
                                 failmsg='', max_lf=3)
    if not out:
        out = nikkyai.markov_forward((fmt[1], 'more', 'like'), failmsg='',
                                     max_lf=3)
        if not out:
            out = '{}\n{}'.format(
                fmt[1],
                nikkyai.markov_forward(('more', 'like', '\n'), failmsg='',
                                       max_lf=2))
    return out


def rule(nikky, fmt):
    seed = choice(("Don't be", "Don't use", "Don't talk", "Don't bring",
                   "Don't mention", "Don't do", "Don't act"))
    chain = nikky.markov.str_to_chain(seed)
    # Do our own repeated response checking--this lets us avoid giving the same
    # “rule” more than once in the same list, even if several are being
    # combined at once into a single output message
    #
    # Caveat:  if this function's output is the only thing output in a table
    # rule, “allow repeats” flag *must* be True (even though repeats are still
    # avoided), else it will loop forever and never output anything (it will
    # check the response here, add it to the list, and then check it again
    # in nikkyai, which will always reject it as a duplicate before ever being
    # output).
    for i in xrange(0, nikky.recurse_limit):
        out = nikky.markov_forward(chain, max_lf=0)
        try:
            return nikky.check_output_response(out, add_response=True)
        except nikkyai.Bad_response_error:
            continue
    return "???"


patterns = (
# Legal forms:
# pattern regexp, priority, action
# pattern regexp, priority, action, allow repeat?
# pattern regexp, last reply, priority, action, allow repeat?

# Basics
(r"\b(hi|hello|hey|sup|what's up|welcome)\b", 0,
    R(
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
    ),
),
(r'\b(brb|be right back)\b', 1, R('k', 'kk')),
(r'\bno\W*thanks\b', 1, R('DIAF then')),
(r'\b(wb|welcome back|welcoem back)\b', 1, R('No\nGo away')),

# General
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
(r'\breboot\b', 1,
    R(
        '\001ACTION reboots {0}\001\nlolrotflrebooted',
        'Or you can start using a halfway decent OS'
    )
),
(r'\bwhere.*you hear that\b', 1, R('Omnimaga', 'your mom', 'your face')),
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
    R('Communism.')
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
(r'\brule\b', 1, E(rule), True),
    #                     ^ Not really allowing repeats (already handled by
    # (rule function; if this is False, it will double-check and fail every
    # response as a duplicate and never output anything.)
(r'\brules\b', 1,
    S(
        R('Rules:', 'Channel rules:', 'Forum rules:', "Today's rules",
          "Today's channel rules:", "Today's forum rules:"),
        '\n1. ', E(rule),
        '\n2. ', E(rule),
        '\n3. ', E(rule),
    )
),
(r'(.*?)\S*more like\S*$', -10, E(more_like)),
(r"^(is|are|am|should|can|do|does|which|what|what's|who|who's)(?: \S+)+[ -](.*?)\W+or (.*)\b", -1,
    S(
        R(
            S('{2}', R(' by far', ', of course', ', naturally', '\nduh')),
            S('{3}', R(' by far', ', of course', ', naturally', '\nduh')),
        ),
        '\n',
        R('', Markov_forward('because', [' ']), Markov_forward('since', [' '])),
    ),
),
(r"(?:is(?: it)?|it's|i'm|i am)\b ([^][.;,!?(){{}}]+)", -1,
    R(
        S(
            R('{0} is', "{0}'s mom is", "{0}'s face is", 'your mom is',
              'your face is', 'you are', "you're"),
            R(' ', '\n'),
            '{1}',
        ),
    ),
),

)
