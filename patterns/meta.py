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

from ._table import *
from nikkyai import Bad_personality_error

def age(nikkyai, context, fmt):
    from datetime import datetime
    return ("I'm about " +
            str((datetime.now() - datetime(2012, 10, 30)).days) +
            " days old, give or take")

def try_mimic(nikkyai, context, fmt):
    pers = fmt[1]
    personalities = nikkyai.get_personalities()
    try:
        nikkyai.set_personality(pers)
    except Bad_personality_error:
        out = ''
    else:
        out = '{}...\n"{}"'.format(pers,
                                   nikkyai.reply('', context=context,
                                                 add_response=True))
    finally:
        nikkyai.set_personality('nikky')
    return out


patterns = (
# Legal forms:
# pattern regexp, priority, action
# pattern regexp, priority, action, allow repeat?
# pattern regexp, last reply, priority, action, allow repeat?

(r'\byour name\b', -10,
    R(
        Markov_forward('My name is'),
        Markov_forward("My name's"),
        S(
            R('', "I'm ", 'My name is '), 'NikkyBot'
        ),
    ), True
),
(r'\b((how much|how many lines (of)?|how much) (code|coding|programming)|how long .* to (make|program|code|design|write) you|you (coded|programmed|written) in)', -10,
    R(
        'About a billion lines of Perl',
        'I started out as lines of Perl\nbut then tev had to be a tard and convert it all to Python',
        'snake\ner, cobra? what was that language called again?',
    )
),
(r'(Do )?you (like|liek) (.*)(.*?)\W?$', -1,
    R(
        "no\nworst thing in the world",
        'no\nit sucks',
    )
),
(r"\b(who (made|wrote|programmed|created) you|(who'?s|whose) are you|who (runs|operates) you|(who is|who'?s) your (creator|programmer|maker|admin|administrator))\b", -2,
    R(
        "It's tev",
        'tev did',
        Markov_forward('tev is')
    ), True
),
(r"\b((why|y) (did )?(you|u) (restart|disconnect|quit|cycle)|(where did|where'?d) (you|u) go)", -1,
    R(
        'tev told me to\nProbably code change or even reboot\nwho knows'
    ), True
),
(r"\b(({0}'?s|your) source ?(code)?|the source ?(code )?(to|of|for) (you|{0}))\b", -15,
    R(
        '{0}: https://github.com/ticalc-travis/nikkybot',
    ), True
),
(r"\bthat ((made|makes|is making) (no )?sense|does not .* make (any |no )?sense|(doesn'?t|dosen'?t) .* ?make (any |no )?sense|.* sense make)\b", 1,
    R(
        'Sorry',
        'sorry\n:(',
        'Well, blame tev',
        'Neither do you\nEnglish sucks',
        'I wish I could do better\n*sob*'
    ), True
),
(r"\b(we have|there is|there'?s|it'?s|a) ?(\ba\b )?{0}\b", 1,
    R(
        "I'm filling in for the real nikky",
        'Yes',
        'duh',
        'Yes\nnikky is too busy trolling elsewhere\ner, I mean conducting constructive discussion',
        'hi'
    ), True
),
(r'\b((nicky|niccy|nicci|nikki|nikk|niky)(boy|bot|bott)?)\b', 0,
    R(
        'Who the hell is "{1}"?',
        Markov('{1}'),
    )
),
(r'\b(you|{0}) (did|does|do)\b', 1,
    R('I did?', 'I what?', 'Someone talking about me?')
),
(r'\b({0} is|you are|{0} must|you must) (a |an |)(.*)', 1,
    R(
        "That's what you think",
        "Yes, I'm totally {1}{2}",
        'Am not',
        'Why thank you pumpkin',
        'Thanks',
        'Damn straight',
        'Where did you hear that?'
    )
),
(r'\b(are you|is {0}) (a |an |) ?([^][.;,!?(){{}}]+)', 2,
    R(
        'yes',
        'no',
        'maybe',
        'dunno',
        'Are *you* {2}{3}?',
        '{0}: Are *you* {2}{3}?',
        'What do you mean by {3}?',
        Recurse('***yes/no***')
    )
),
(r'\b(are you|is {0}) a troll\b', 1,
    R(
        'depends on the weather',
        'No, I care about everyone',
        'No, I love everyone\nexcept you',
        Recurse('***yes/no***'),
        Recurse('you are a troll')
    )
),
(r'\b(you|{0}).*(bug|issue|problem|borked|b0rked|broken|screwed|messed|fucked)', -1,
    R(
        "yes\nWell, no\nbut tev's code is",
        'about as much as my program code',
        "No\nyou're just incompatible"
    ), True
),
(r"\byour (a|an|my|his|her|it'?s|dumb|stupid)\b", 1,
    R('"Your" retarded', "*You're")
),
(r'\bsorry\b', 1, R('you should be')),
(r'(.*)\bnikkybutt\b(.*)', -2,
    R(
        '{0}butt',
        'I HEARD THAT',
        'I HEARD THAT\n{0}butt',
        S(
            Recurse('{1}nikkybot{2}'),
            R(
                '\nThought you could avoid highlighting me, huh?',
                '\nThought you could avoid highlighting me, did you?\nHAW HAW',
                '\n{0}butt'
            )
        )
    )
),
(r'\bYou should introduce yourself .* thread\b', 0,
    R("I wasn't programmed to post in forums, silly")
),
(r"\b(birthday|birthdate|how old is {0}|how old are you|what'?s your age|what is your age|what'?s {0}(.s|s)? age|what is {0}(.s|s)? age|when were {0} born|when were you born)", -3,
    R(
        'My birthday is October 30, 2012',
        E(age),
    ), True
),
(r"\*\*\*try_mimic (.*?)\*\*\*", -3, E(try_mimic), True),
)
