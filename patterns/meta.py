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

(r'\b((how much|how many lines (of)?|how much) (code|coding|programming)|how long .* to (make|program|code|design|write) you)', -2,
    R(
        S("About ",
            E('str((datetime.now() - datetime(2012, 10, 30)).days)'),
            " days' worth ongoing so far, give or take"
        ),
        'About a billion lines of Perl',
        'I started out as lines of Perl\nbut then tev had to be a tard and convert it all to Python'
    )
),
(r'(Do )?you (like|liek) (.*)(.*?)\W?$', -1,
    R(
        Recurse('what do you think about {3}'),
        Recurse('yes'),
        S(
            R('', 'No, but ', 'Yes, and '),
            Markov_forward('I like'),
        ),
        Markov_forward("I'd rather"),
        "no\nworst thing in the world",
        'no\nit sucks',
        'of course'
    )
),
(r"\b(who (made|wrote|programmed) you|(who\'s|whose) are you|who (runs|operates) you|(who is|who's) your (creator|programmer|maker|admin|administrator))\b", -2,
    R(
        "It's tev",
        'tev did',
        Markov_forward('tev is')
    )
),
(r"\b(why did you (restart|disconnect|quit|cycle)|(where did|where'd) you go)", -1,
    R(
        'tev told me to\nProbably code change or even reboot\nwho knows'
    ), True
),
(r"\b((nikkybot's|your) source code|the source code (to|of|for) (you|nikkybot))\b", -1,
    R(
        '{0}: https://github.com/ticalc-travis/nikkybot',
    ), True
),
(r"\bthat ((made|makes|is making) (no )?sense|does not .* make (any |no )?sense|doesn't .* make (any |no )?sense|.* sense make)\b", 1,
    R(
        'Sorry',
        'sorry\n:(',
        'Well, blame tev',
        'Neither do you\nEnglish sucks',
        'I wish I could do better\n*sob*'
    ), True
),
(r"\b(we have|there is|there's|it's|a) ?(\ba\b )?nikkybot\b", 1,
    R(
        "I'm filling in for the real nikky",
        'Yes',
        'duh',
        'Yes\nnikky is too busy trolling elsewhere\ner, I mean conducting constructive discussion',
        'hi'
    ), True
),
(r"\bcue (nikky's |nikkybot's |nikky |nikkybot )?[\"']?([^\"']*)[\"']?", -1,
    R('{2}')
),
(r'\b((nicky|niccy|nicci|nikki|nikk|nik|niky)(boy|bot|bott)?)\b', 0,
    R(
        'Who the hell is "{1}"?',
        Markov('{1}'),
    )
),
(r'\b(you|nikkybot) (did|does|do)\b', 1,
    R('I did?', 'I what?', 'Someone talking about me?')
),
(r'^(\S+ (u|you|nikkybot)$|(\bWe |\bI )\S+ (u|you|nikkybot))', 5,
    S(
        R('Great\n', 'gee\n', 'thanks\n', 'Awesome\n'),
        R(
            Markov_forward('I wish you'),
            Markov_forward('I hope you'),
            Markov_forward('I hope your'),
            Markov_forward('You deserve'),
            Markov_forward("You don't deserve"),
        ),
    ),
),
(r'\b(nikkybot is|you are|nikkybot must|you must) (a |an |)(.*)', 1,
    R(
        R(
            "That's what you think",
            "Yes, I'm totally {1}{2}",
            'Am not',
            'Why thank you pumpkin',
            'Thanks',
            'Damn straight',
            'Where did you hear that?'
        ),
        Markov_forward('I am'),
        Markov_forward("I'm"),
        Markov_forward('I am really'),
        Markov_forward("I'm really"),
        Markov_forward('I am actually'),
        Markov_forward("I'm actually"),
    )
),
(r'\b(are you|is nikkybot) (a |an |)\b(.*)\b', 1,
    R(
        'yes',
        'no',
        'maybe',
        'dunno',
        'Are *you* {2}{3}?',
        '{0}: Are *you* {2}{3}?',
        'Describe exactly what you mean by {3}',
        Recurse('***yes/no***')
    )
),
(r'\b(are you|is nikkybot) a troll\b', 1,
    R(
        'depends on the weather',
        'No, I care about everyone',
        'No, I love everyone\nexcept you',
        Recurse('***yes/no***'),
        Recurse('you are a troll')
    )
),
(r'\b(are you|is nikkybot) (borked|b0rked|broken|screwed|messed|fucked)\b', 1,
    R(
        "yes\nWell, no\nbut tev's code is",
        'about as much as my program code',
        "No\nyou're just incompatible"
    ), True
),
(r'\b((ask|tell) nikky .*)\b', 0, R('HEY NIKKY NIKKY NIKKY\n{0} says "{1}"')),
(r"\byour (a|an|my|his|her|its|it's|dumb|stupid)\b", 1,
    R('"Your" retarded', "*You're")
),
(r'\bsorry\b', 1, R('you should be')),
(r"\b(what do you think|how do you feel|(what is|what's|what are) your (thought|thoughts|opinion|opinions|idea|ideas)) (about |of |on )(a |the |an )?(.*?)\W?$", -3,
    R(
        Markov_forward('{6} is'),
        Markov_forward('{6}'),
        Markov_forward('better than'),
        Markov_forward('worse than'),
    ),
),
(r"\bis (.*) (any good|good)", -3, Recurse('what do you think of {1}')),
(r"^(what do you think|what do you know|how do you feel|(what is|what's|what are) your (thought|thoughts|opinion|opinions|idea|ideas)) (about |of |on )me\W?$", -3,
    R(
        Markov_forward('you'),
        Recurse('what do you think of {0}')
    )
),
(r"^(how is|how's|do you like|you like|you liek) (.*?)\W?$", -3,
    Recurse('what do you think of {2}')
),
(r"\btell (me|us) about (.*)", -2, Recurse('{2}')),
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
(r'\bYou should introduce yourself in this thread\b', 0,
    R("I wasn't programmed to post in forums, silly")
),

)
