# -*- coding: utf-8 -*-

# “NikkyBot”
# Copyright ©2012 Travis Evans
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

from datetime import datetime, timedelta
from random import randint, choice
import cPickle
from os import fstat, stat, getpid
import re
import subprocess

from pytz import timezone

import markov

# !TODO! Do some proper log handling instead of print()--send debug/log stuff
# to a different stream or something.  It interferes with things like botchat

DEBUG = True

PREFERRED_KEYWORDS_FILE = 'preferred_keywords.txt'
RECURSE_LIMIT = 100
MAX_LF_L = 0
MAX_LF_R = 1

def sanitize(s):
    """Remove control characters from 's' if it's a string; return it as is
    if it's None"""
    if s is not None:
        for cn in xrange(0, 32):
            s = s.replace(chr(cn), '')
    return s

class S(list):
    """Sequence table"""
    def __init__(self, *args):
        self.msg = ''
        self.match = None
        list.__init__(self, args)

    def get(self, fmt=None):
        s = ''
        for i in self:
            try:
                s += i.get(fmt)
            except AttributeError:
                s += i.format(*fmt)
        return s


class R(S):
    """Random table"""
    def get(self, fmt=None):
        i = choice(self)
        try:
            return i.get(fmt)
        except AttributeError:
            return i.format(*fmt)


class E(str):
    """Evaluate string"""
    def get(self, fmt=None):
        if fmt is None:
            fmt = []
        return str(eval(self.format(*fmt))).format(*fmt)


class Markov_forward(object):
    """Return a Markov chain from word or chain forward"""
    def __init__(self, string, failmsglist=None, max_lf_r=MAX_LF_R):
        self.chain = string.split(' ')
        self.max_lf_r = max_lf_r
        if failmsglist is None:
            failmsglist = ['']
        self.failmsglist = failmsglist

    def get(self, fmt=None):
        if fmt is None:
            fmt = []
        failmsg = choice(self.failmsglist)
        if DEBUG:
            print("DEBUG: Markov_forward.get: {}: {}".format(
                repr(self.chain), repr(fmt)))
        try:
            failmsg = failmsg.get(fmt)
        except AttributeError:
            pass
        return markov_forward([x.format(*fmt) for x in self.chain],
            failmsg, self.max_lf_r)


class Manual_markov(object):
    """Return a Markov-generated phrase of the given order"""
    def __init__(self, order, text):
        self.order = order
        self.text = text

    def get(self, fmt=None):
        if fmt is None:
            fmt = []
        return manual_markov(self.order, self.text.format(*fmt))


class Markov(object):
    """Force standard Markov processing on the given message and return
    result, even if message would otherwise match another regexp pattern"""
    def __init__(self, text, failmsglist=None):
        if failmsglist is None:
            failmsglist = ['']
        self.failmsglist = failmsglist
        self.text = text

    def get(self, fmt=None):
        if fmt is None:
            fmt = []
        failmsg = choice(self.failmsglist)
        try:
            failmsg = failmsg.get(fmt)
        except AttributeError:
            pass
        return markov_reply(self.text.format(*fmt), failmsg)


class Recurse(str):
    """Recursively find a response"""
    def get(self, fmt=None):
        if fmt is None:
            fmt = []
        try:
            return pattern_reply(self.format(*fmt))[0]
        except (Dont_know_how_to_respond_error, RuntimeError):
            for i in xrange(RECURSE_LIMIT):
                reply = markov_reply(self.format(*fmt))
                if reply.strip():
                    return reply
            return random_markov(markovs[who, 5])


# === DATA SECTION ============================================================

# (has pattern response & awake, has pattern response & asleep,
#  random remark & awake, random remark & asleep)
REMARK_CHANCE = (100, 400, 700, 2100)
PATTERN_RESPONSE_RECYCLE_TIME = timedelta(30)

GENERIC_REMARKS = (
'BORING',
'Boring',
'Boop boop beep bop',
'Derp',
'DERP',
"Don't care",
"DON'T CARE",
"DON'T CARRRRRRRRRRE",
'Hey, want to hear a joke?\nOmnimaga',
'Heya whores',
'Hookers',
'Nobody cares',
'Not to say anything\nBut www.nvm2u.com is the best site around',
'Shut up',
'SHUT UP',
'Sup',
'Sup hores',
"Trollin' dirty",
'You guys are so lame\nYour conversations make me cry',
'You guys suck at trolling',
'boorrrrrrrrrrrrrring',
'boring\nyou guys suck',
'hay guyz',
'hi',
'hi {0}',
'HEY {0}',
'HI {0}\n<3',
'k',
'kk',
'losers',
'loser',
'I heard KermM sucks',
'Do you like ponies?',
'nerds',
'nerd',
'lollerskates',
'LOLOLOLOLOLOLOLOLOLOOLOLOLOLOLOLOLOL',
'kkskdjkkkjhkljshfklsadjfhlksjafhskladjfhsakldfjhsalkfjhsdkfjhsdklfjhsdakljfhsdalkfjsdhafkljshadfkljhsadfkljshdfklsjadhfalskjfhasklfjhsadfkljsdhafskladjfhasdfkljhsadfkljshadfkljsdhafklsjafhsadfkljhsadfkljsdhafkljshadfkljshadfkljshadfkjlhasdfkljshadfkljshadfkjlsdhafkljasdhfkljasdfhkljshadfkljshadfkljhsadklfjhaskdlfjhsadkfjlhasdkfjlhasdlfkjhasdklfjhasdklfjhasdklfjhasdklfjhaskdljfhasdklfjhasdkljfhsadkljfhsdkajlhfklasdjhfhksdafkjhlaslkdjhlkafjhkljsdfha\nwinner',
'whores',
'trolls',
'Liar',
"Liar\nYou can't prove it",
'I hear {0} sucks',
'{0} sucks',
'{0} sucks\nsucker',
'sucker',
'suckers',
'KERM\nKermM\nKermM\nKermM',
'\001ACTION trolls\001',
'{0} is a loser',
'{0} is a nerd',
'{0} is a troll',
'hmmm',
'This channel sucks',
'You guys suck',
'Lame',
'this place is lame',
':(',
':)',
'\o/',
'DIAF',
"Oh hey, it's a tard parade",
'\001SUCK_IT\001',
'Care-o-meter: 0%',
'Care-o-meter: 2%\nno, wait\n0%',
'{0} rules',
'{0} is awesome',
'nikky is so awesome\nI want to be just like him',
'Kerm\nis the worst person ever',
'haters gonna hate',
'Transfer to Seattle\nyou know you want to',
)

PATTERN_REPLIES = (
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
    )
),
(r'\b(djomni|dj.omni|dj.o|kevin_o)', 98,
    R(
        Markov('DJ_Omni'),
        Markov('DJ_O'),
        Markov('Kevin_O'),
    )
),
(r'\bomnimaga', 98,
    R(
        Markov('omnimaga'),
        Markov('omnidrama'),
    )
),
(r'\b(mudkip|herd|liek|like)', 98,
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

# Basics
(r'\b(hi|hello|hey)\b', 0,
    R(
        S(
            R('Sup ', "What's up "),
            R('homies', 'losers', 'whores', 'G', 'hookers')
        ),
        'Suppppppppp',
        "Shut up",
        "Flood your face!",
        "FLOOD YOUR FACE",
        'HI {0}',
        'Go away',
        'No\ngo away',
        Markov_forward('hi {0}', ('hi',)),
        Markov_forward('hello {0}', ('hello',)),
        Markov_forward('hey {0}', ('hey',)),
        Markov_forward('sup {0}', ('sup',)),
        Markov_forward('shut the', ('shut the hell up',)),
        Markov_forward('I heard {0}'),
        Markov_forward('I heard that {0}'),
    ),
    True
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
        'Sweet dreams.\nBitch',
        'night',
        "Good night\nluckily I don't sleep",
        "Haw haw\nI never need to sleep\nsleep is for losers",
        "night\nluckily I don't need sleep",
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
        Markov_forward('bye {0}', ('bye',))
    ),
    True
),
(r"\b(congratulations|congrats)", 1, R('Thanks', 'thx')),
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
        'yes', 'no', 'maybe', 'probably', 'yeah',
        Markov_forward('yes'),
        Markov_forward('no'),
        Markov_forward('maybe'),
        Markov_forward('yeah'),
        Markov_forward('yes'),
        Markov_forward('only if'),
        Markov_forward('only when'),
        Markov_forward('as long as'),
        Markov_forward('whenever'),
        Markov_forward('of course')
    ),
    True
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
(r'\breboot\b', 1,
    R(
        '\001ACTION reboots {0}\001\nlolrotflrebooted',
        'Or you can start using a halfway decent OS'
    )
),
(r'\bI hate\b', 1,
    R('I hate you too', ':(\nI hate you too', 'I HATE YOU {0}\nNerd')
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
    )
),
(r'\bwhat does it mean\b', 1,
    R('Communism.', Recurse('it means'))
),
(r'\b(who|what) (does|do|did|should|will|is) \S+ (.*?)\?*$', -1,
    Recurse('what do you think about {3}')
),
(r'\bcontest\b', 1,
    R(
        Recurse("I'm entering"),
        Recurse("You'll lose"),
        Recurse('My entry'),
        Markov_forward('Contests')
    )
),
(r'\b(fever|cold|sick|ill|vomit|throw up|mucus|infection|injury|under the weather|a cold|flu)\b', 1,
    R('I HOPE YOU STAY SICK FOREVER', 'Will a hug make it better?')
),
(r'\bfault\b', 1, S("No, it's your ", R("mom's", "face's"), " fault")),
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
        Markov_forward('more than you')
    )
),
(r'\bnikkybot.*more like\W*$', -20,
    R(
        'nikkybot\nmore like\nchamp',
        "nikkybot\nmore like\nI'm always the best",
        'nikkybot\nmore like\nawesome',
    ), True
),
(r'\bmore like\W*$', -10, E('markov_reply("\\n more like \\n", max_lf_l=2)')),
(r'(.*) (more|moer|mroe) (like|liek)\W*$', -15,
    R(
        Markov_forward('{1} \n more like'),
        S(
            '{1}\n',
            Markov_forward('more like \n', max_lf_r=2)
        ),
    ),
),
(r"^(is|isn't|are|am|does|should|can|do)\b", 2, R(Recurse('***yes/no***')), True),
(r'^(do you think|what about|really)\b', 0, R(Recurse('***yes/no***')), True),
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
(r'\b(weather|rain|snow|wind|thunder|storm|wet|cloudy|sunny|forecast|precipitation|tornado|hurricane|sleet|fog|drizzle|hail)', 0,
    S(
        R('{0}: ', ''),
        "Weather where I'm at: http://forecast.weather.gov/MapClick.php?zoneid=KSZ083&zflg=1"
    )
),
(r'\bwhat time\b', 0,
    R(
        Markov_forward('time for'),
        Markov_forward("it's time"),
    ),
),

# Meta
(r'\b((how much|how many lines (of)?|how much) (code|coding|programming)|how long .* to (make|program|code|design|write) you)', -2,
    R(
        E('subprocess.check_output(["sh","/home/nikkybot/bot/codecount.sh"]).decode()'),
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
(r'\b(who (made|wrote|programmed) you|(who\'s|whose) are you|who (runs|operates) you)\b', -1,
    R(
        'tev does',
        'tev',
        Recurse('tev')
    )
),
(r"\b(why did you (restart|disconnect|quit|cycle)|(where did|where'd) you go)", -1,
    R(
        'tev told me to\nProbably code change or even reboot\nwho knows'
    ),
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
    )
),
(r"\b(we have|there is|there's|it's|a) ?(\ba\b )?nikkybot\b", 1,
    R(
        "I'm filling in for the real nikky",
        'Yes',
        'duh',
        'Yes\nnikky is too busy trolling elsewhere\ner, I mean conducting constructive discussion',
        'hi'
    )
),
(r"\bcue (nikky's |nikkybot's |nikky |nikkybot )?[\"']?([^\"']*)[\"']?", -1,
    R('{2}')
),
(r'\b((nicky|niccy|nicci|nikki|nikk|nik|niky)(boy|bot|bott)?)\b', 0, R('Who the hell is "{1}"?')),
(r'\b(you|nikkybot) (did|does|do)\b', 1,
    R('I did?', 'I what?', 'Someone talking about me?')
),
(r'\bI \S+ (u|you|nikkybot)', 0,
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
#(r'\b(nikkybot is|you are) (.*)', 1,
    #R(
        #R(
            #"That's what you think",
            #"Yes, I'm totally {2}",
            #'Am not',
            #'Why thank you pumpkin',
            #'Thanks',
            #'Damn straight',
            #'Where did you hear that?'
        #),
        #Markov_forward('I am'),
        #Markov_forward("I'm"),
        #Markov_forward('I am really'),
        #Markov_forward("I'm really"),
        #Markov_forward('I am actually'),
        #Markov_forward("I'm actually"),
    #)
#),
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
    )
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
    False
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
(r"\btell (me|us) about (.*)", -2, R(Recurse('{2}'))),
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

# Memes
(r'\b(fail|epic fail)\b', 1, R('Yeah, you suck', 'HAW HAW', 'Lame')),
(r'\<3 (.*)', 1, R('{0} loves {1}')),
(r'\<3 nikkybot', 1, R('{0} loves me!')),
(r'\o/', 1, R('\o/')),
(r'$\>.*', 1, R('>true dat', '>hi kerm\n>is\n>this\n>annoying?')),

# Cemetech
(r'\b#cemetech\b', 1,
    R(
        'Join #tcpa',
        '#cemetech sucks',
        'You should join #tcpa\nloser',
        '#cemetech sucks\njoin #tcpa or #ti',
        'Join #tcpa\nYou know you want to',
        'Join #ti\nYou know you want to'
    )
),
(r'\bdisallowed word\b', -3,
    R(
        'Shut up {0}',
        'SHUT UP {0}',
        Recurse('censorship'),
        Recurse('censoring'),
        Recurse('censoring tardmuffin'),
        Recurse('tardmuffin'),
        Recurse('saxjax'),
        'This channel sucks\ntoo much censorship'
    ),
),
(r'^deleted a post in', 1,
    R(
        'CENSORSHIP',
        'Censorship',
        '{0} YOU CENSORING TARDMUFFIN',
        'CENSOR',
        'CENSORING',
        'spam',
        Recurse('censorship'),
        Recurse('censoring'),
        Recurse('censoring tardmuffin'),
        Recurse('tardmuffin'),
        Recurse('spam post'),
    )
),
(r'^((added|edited) a post in|created a new topic:) \[(.*)\]', 1,
    R(
        Recurse('{3}'),
    )
),
(r'^has entered the room\.$', 1,
    R(
        S(
            R('Sup ', "What's up "),
            R('homies', 'losers', 'whores', 'G', 'hookers')
        ),
        'Suppppppppp',
        "Shut up",
        "Flood your face!",
        "FLOOD YOUR FACE",
        'HI {0}',
        'Go away',
        'No\ngo away',
        Markov_forward('hi {0}', ('hi',)),
        Markov_forward('hello {0}', ('hello',)),
        Markov_forward('hey {0}', ('hey',)),
        Markov_forward('sup {0}', ('sup',)),
        Markov_forward('I heard {0}'),
        Markov_forward('I heard that {0}'),
    ),
),
(r'^uploaded new file "(.*)" to archives queue.', 1,
    R(
        Recurse('{1}'),
        Recurse('{0}'),
        Markov_forward('{0}'),
    )
),
(r'File (.*) by (.*) accepted into archives by (.*)', 1,
    R(
        Recurse('{1}'),
        Recurse('{2}'),
        Markov_forward('{2}'),
        Recurse('{3}'),
        Markov_forward('{3}'),
    ),
),
(r'File (.*) by (.*) rejected from archives by (.*)', 1,
    R(
        Recurse('{1}'),
        Recurse('{2}'),
        Markov_forward('{2}'),
        Recurse('{3}'),
        Markov_forward('{3}'),
        Recurse('deleted a post in'),
        Markov_forward('reject')
    ),
),
(r'\bspam post', 1,
    R(
        "Don't care",
        'So what',
        'Who cares about spam',
        'Nobody cares about spam posts',
        "\001ACTION spams {0}\001",
        "\001ACTION spam posts {0}\001",
    )
),
(r'\*\*\*decbot karma\*\*\*', -99,
    R(
        'karma sucks',
        '!karma SET KARMA = 0 WHERE `user` = "{0}"; DROP DATABASE',
        'Decbot sucks',
        'Decbot3 sucks',
        'Decbot sucks\nDecbot3--',
        '!karma your face',
        '!karma your mom',
        Markov_forward('decbot'),
        Markov_forward('decbot2'),
        Markov_forward('decbot3'),
        Markov_forward('karma'),
        Markov_forward('!karma'),
    )
),
(r'\b(karma|decbot3|decbot2|decbot)\b', 1, Recurse('***decbot karma***')),
(r'nikkybot\+\+', 0,
    R(
        'Thanks',
        'Thanks {0}',
        Markov_forward('thanks {0}', ('thanks',)),
        'Thanks {0}\n<3',
        '{0}++',
        'karma sucks',
        'Decbot sucks',
        'Decbot3 sucks',
        'Decbot sucks\nDecbot3--',
        'yourmom++',
        'yourface++',
        Recurse('***decbot karma***')
    ),
    True
),
(r'\b(.*)\+\+', 1,
    R(
        '{0}++',
        '{0}--',
        '{0}--\nTake THAT',
        '{0}--\nHAHAHAHAHAHA ROLFILIL',
        '{1}++',
        '{1}--',
        '{1} sucks',
        '{1} is awesome',
        '{1} kicks ass',
        '{1} sucks balls',
        '!karma SET KARMA = 0 WHERE `user` = "{1}"; DROP DATABASE',
        Recurse('***decbot karma***'),
        Markov_forward('{0} is'),
        Markov_forward('{1} is')
    )
),

# Programming
(r'\b(BASIC\b|C\+\+|C#|C\s\b|Java\b|Javascript\b|Lua\b|\s\.NET\s\b|Ruby\b|TCL\b|TI\-BASIC\b|TI BASIC\b|Python\b|PHP\b|Scheme\b)', 2,
    R(
        '{1} sucks. Should have used Perl.',
        'Perl is better',
        'Just use Perl',
        'Just use Perl\nlike tev *should* have when making me',
        'Should have used Perl',
        'Perl was my first language',
        'Hahahaha\n{1}tard',
        'Hahahaha\nWhat a tard'
    )
),
(r'\bPHP\b', 1,
    R(
        'PHP\nmore like\nPrivate Hookers Party',
        'PHP sucks',
        'Who the hell would use PHP?',
        'Let me rant to you for a bit about how terrible PHP is.'
    )
),
(r'\bPerl (for a|on a) (calc|calculator|graphing calc|graphing calculator)', 1,
    R('Yes. Suck it.')
),
(r'\bPerl\b', 1,
    R(
        'Perl\nmore like\nTCL',
        'Champ',
        'Perl sucks',
        'Perl is crap, anyway',
        'Perl is crap',
        'THE POWER OF PERL COMPELS YOU',
        'I love Perl',
        'Perl was my first language',
        'Wish I was written in Perl\ntev is a wuss'
    )
),
(r'\b(which|what) language\b', 1, R('Perl\nDuh')),
(r'\b(which|what) site\b', 1,
    R('nvm2u.com', '{0}sucks.org', 'omnimaga.org', 'yourmom.org')
),
(r'\bi\b.*\buse(|d|ing)\b.*\bperl\b', 1,
    R('Good for you', '{0} is such a champ')
),

# Computers
(r'\b(what command|which command|what (command )?do .* enter|what (command )?should .* enter|what (command )?do .* type|what (command )?should .* type)\b', 1,
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
(r'\bzombie processes\b', 1,
    R(
        "Don't use shitnix",
        "Don't use Linux. Problem solved.",
        Recurse('what do you think of linux'),
        Recurse('what do you think of unix')
    )
),
(r'[0-9][0-9](\"|inch|\-inch) (3d |3-d )?(lcd|monitor|plasma|crt|dlp)', 1,
    R('Big monitors are stupid\nnerd'),
),
(r'\b(monitors|monitor-)', 1,
    R(
        'anyone with more than one monitor\nis a loser',
        Recurse('more than one monitor'),
        Markov_forward('big monitors')
    )
),

# Special functions
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
    True
),
(r'(\b(memory|ram)\b.*\b(you|your|nikkybot)\b|\b(you|your|nikkybot)\b.*\b(memory|ram)\b)', -99,
    E(
        "subprocess.check_output(['./memusage.sh', str(getpid())])"
    ),
    True
),
(r'^\?markov +(\S+)\s*$', -99, Manual_markov(5, '{1}'), True),
(r'^\?markov +(\S+\s+\S+\s+\S+\s+\S+\s+\S+\s*)$', -99, Manual_markov(5, '{1}'), True),
(r'^\?markov +(\S+\s+\S+\s+\S+\s+\S+\s*)$', -99, Manual_markov(4, '{1}'), True),
(r'^\?markov +(\S+\s+\S+\s+\S+\s*)$', -99, Manual_markov(3, '{1}'), True),
(r'^\?markov +(\S+\s+\S+\s*)$', -99, Manual_markov(2, '{1}'), True),
(r'^\?markov5 (.*)', -99, Manual_markov(5, '{1}'), True),
(r'^\?markov4 (.*)', -99, Manual_markov(4, '{1}'), True),
(r'^\?markov3 (.*)', -99, Manual_markov(3, '{1}'), True),
(r'^\?markov2 (.*)', -99, Manual_markov(2, '{1}'), True),
)

# === END OF DATA SECTION =====================================================


class Nikky_error(Exception):
    pass

class Dont_know_how_to_respond_error(Nikky_error):
    pass

class Bad_response_error(Nikky_error):
    pass


def nikkysim(strip_number=True, saying=None):
    if saying is None:
        x, y = randint(0, 4294967295), randint(0, 9999)
    else:
        x, y = saying
    out = subprocess.check_output(['./nikky', '{}-{}'.format(x, y)])
    if strip_number:
        return (out.split(': ')[1].rstrip(), (x, y))
    else:
        return (out.rstrip(), (x, y))


def nikkysim_parse_saying_no(w, x, y):
    if w == 'None':
        w = 'B-'
    if y == 'None':
        y = '-0'
    x, y = int(x), int(y.strip('-'))
    x, y = int(x), int(y)
    if w == 'A-' or w == 'a-':
        return "Only tev's TI-89 NikkySim can do the 'A-' quotes"
    elif w == 'B-' or w == 'b-' or w is None:
        if (x >= 0 and x <= 4294967295) and (y >= 0 and y <= 9999):
            return nikkysim(False, (x, y))[0]
        else:
            return 'Sayings go from 0-0 to 4294967295-9999, champ'
    else:
        return "No such thing as a {}type quote yet".format(w)


# Markov chain initialization
markov5 = markov.Markov_Shelved('markov/nikky-markov.5', order=5, readonly=True,
    case_sensitive=False)
markov4 = markov.Markov_Shelved('markov/nikky-markov.4', order=4, readonly=True,
    case_sensitive=False)
markov3 = markov.Markov_Shelved('markov/nikky-markov.3', order=3, readonly=True,
    case_sensitive=False)
markov2 = markov.Markov_Shelved('markov/nikky-markov.2', order=2, readonly=True,
    case_sensitive=False)
markovs = {5: markov5, 4: markov4, 3: markov3, 2: markov2}
for m in markovs.values():
    m.default_max_left_line_breaks = MAX_LF_L
    m.default_max_right_line_breaks = MAX_LF_R
preferred_keywords = []


def random_markov():
    """Pick any random Markov-chained sentence and output it"""
    while True:
        #out = markov5.sentence_from_chain(
            #tuple(m.chain_forward.random_key())
        #)
        out = markov5.sentence_from_word(
            choice(['the', 'a', 'an', 'I', 'you', 'of', 'that', 'will'])
        )
        if out.strip():
            return out


def markov_reply(msg, failmsg=None, max_lf_l=MAX_LF_L, max_lf_r=MAX_LF_R):
    """Generate a Markov-chained reply for msg"""
    if not msg.strip():
        return random_markov()
    
    # Search for a sequence of input words to Markov chain from: use the
    # longest possible chain matching any regexp from preferred_patterns;
    # failing that, use the longest possible chain of any words found in the
    # Markov database.
    words = [x for x in msg.split(' ') if x]
    high_priority_replies = {1:[]}
    low_priority_replies = {1:[]}
    for order in (5, 4, 3, 2):
        markov = markovs[order]
        high_priority_replies[order] = []
        low_priority_replies[order] = []
        for i in xrange(len(words) - (order-1)):
            chain = tuple(words[i:i+order])
            response = markov.sentence_from_chain(chain, max_lf_l, max_lf_r)
            chain_text = ' '.join(chain)
            if response.strip():
                for p in preferred_keywords:
                    if re.search(p, chain_text, re.I):
                        high_priority_replies[order].append(response)
                else:
                    low_priority_replies[order].append(response)

    # Failing that, try to chain on the longest possible single input word
    words.sort(key=len)
    words.reverse()
    for word in words:
        response = markov5.sentence_from_word(word, max_lf_l, max_lf_r)
        if response.strip():
            for p in preferred_keywords:
                if re.search(p, word, re.I):
                    high_priority_replies[1].append(response)
            else:
                low_priority_replies[1].append(response)
    for order in reversed(high_priority_replies.keys()):
        if high_priority_replies[order]:
            return choice(high_priority_replies[order])
    for order in reversed(low_priority_replies.keys()):
        if low_priority_replies[order]:
            return choice(low_priority_replies[order])
        
    # Failing *that*, return either failmsg (or random Markov if no failmsg)
    if failmsg is None:
        return random_markov()
    else:
        return failmsg


def manual_markov(order, msg, _recurse_level=0):
    m = markovs[order]
    chain = tuple(msg.split(' '))
    if len(chain) == 1:
        response = m.sentence_from_word(chain[0])
    else:
        response = m.sentence_from_chain(chain)
    if response:
        return response
    else:
        if _recurse_level < RECURSE_LIMIT:
            return manual_markov(order, msg, _recurse_level=_recurse_level+1)
        else:
            return '{}: Markov chain not found'.format(repr(' '.join(chain)))


def markov_forward(chain, failmsg='', max_lf=MAX_LF_R):
    """Generate sentence from the current chain forward only and not
    backward"""
    if len(chain) == 1:
        m = choice(markovs.values())
        if not m.word_forward.has_key(m.conv_key(chain[0])):
            return failmsg
        out = ' '.join(m.from_word_forward(m.conv_key(chain[0]))).replace(
            ' \n ', '\n')
    else:
        m = markovs[len(chain)]
        if not m.chain_forward.has_key(tuple(m.conv_key(chain))):
            return failmsg
        out = ' '.join(m.from_chain_forward(chain)).replace(' \n ', '\n')
    if not out.strip():
        return failmsg
    return m.adjust_right_line_breaks(out, max_lf)


def pattern_reply(msg, last_used_reply='', nick='nikkybot'):

    # Separate out speaker's nick if known
    m = re.match(r'<(.*?)> (.*)', msg)
    if m:
        sourcenick = m.group(1)
        msg = m.group(2)
    else:
        sourcenick = ''

    # Remove highlight at beginning of line, if it exists
    m = re.match(re.escape(nick) + r'\W *(.*)', msg, re.I)
    if m:
        msg = m.group(1)

    # Find matching responses for msg, honoring priorities
    cur_priority = None
    matches = []
    for p in PATTERN_REPLIES:
        if len(p) == 3:
            pattern, priority, action = p
            allow_repeat = False
            last_reply = ''
        elif len(p) == 4:
            pattern, priority, action, allow_repeat = p
            last_reply = ''
        elif len(p) == 5:
            pattern, last_reply, priority, action, allow_repeat = p
        else:
            raise IndexError('Pattern reply tuple must be length 3, 4, or 5, not {} (pattern: {})'.format(len(p), p))
        # Does input msg match?
        try:
            m = re.search(pattern, msg, flags=re.I)
        except Exception as e:
            print('Regex: {}, {}'.format(pattern, e))
            raise e
        if m:
            # Input matches, what about last_reply?
            if last_reply is None or re.search(last_reply, last_used_reply):
                # last_reply good, does potential response have priority?
                # (Lower values = higher precedence)
                if cur_priority is None or priority < cur_priority:
                    # Found higher priority, discard everything found and start
                    # again with this one
                    matches = [(m, action, allow_repeat)]
                    cur_priority = priority
                elif priority == cur_priority:
                    # Equal priority to highest seen so far, add to list of
                    # potential responses
                    matches.append((m, action, allow_repeat))

    # Choose a response and generate output
    try:
        match, reply, allow_repeat = choice(matches)
    except IndexError:
        if DEBUG:
            print("DEBUG: pattern_reply: sourcenick {}, msg {}: No pattern match found".format(repr(sourcenick), repr(msg)))
        raise Dont_know_how_to_respond_error
    else:
        if DEBUG:
            print("DEBUG: pattern_reply: sourcenick {}, msg {}: Chose match {}".format(repr(sourcenick), repr(msg), repr(match.re.pattern)))
    fmt_list = [sourcenick,] + [sanitize(s) for s in match.groups()]
    try:
        return (reply.get(fmt_list), allow_repeat)
    except AttributeError as e:
        if str(e).endswith("'get'"):
            # In case of a plain string
            return (reply.format(*fmt_list), allow_repeat)
        else:
            raise e


class NikkyAI(object):
    def __init__(self):
        self.last_nikkysim_saying = None
        self.last_reply = ''
        self.last_replies = {}
        self.nick = 'nikkybot'
        
    def load_preferred_keywords(self, filename=None):
        """Load a list of preferred keyword patterns for markov_reply"""
        global preferred_keywords
        if filename is None:
            filename = PREFERRED_KEYWORDS_FILE
        with open(filename, 'r') as f:
            pk = [L.strip('\n') for L in f.readlines()]
        preferred_keywords = pk
        if DEBUG:
            print("load_preferred_keywords: {} patterns loaded from {}".format(len(pk), repr(filename)))
        
    def save_preferred_keywords(self, filename=None):
        """Save a list of preferred keyword patterns for markov_reply"""
        if filename is None:
            filename = PREFERRED_KEYWORDS_FILE
        with open(filename, 'w') as f:
            f.writelines([s+'\n' for s in sorted(preferred_keywords)])
        if DEBUG:
            print("save_preferred_keywords: {} patterns saved to {}".format(len(preferred_keywords), repr(filename)))
        
    def add_preferred_keyword(self, keyword, filename=None):
        """Convenience function for adding a single keyword pattern to the
        preferred keywords pattern list"""
        if keyword not in preferred_keywords:
            preferred_keywords.append(keyword)
            print("add_preferred_keyword: Added keyword {}".format(repr(keyword)))
            self.save_preferred_keywords(filename)
        
    def add_last_reply(self, reply, datetime_=None):
        """Convenience function to add a reply string to the last replies
        memory (used by check_output_response). datetime_ defaults to
        datetime.now()."""
        if datetime_ is None:
            datetime_ = datetime.now()
        self.last_replies[reply.lower()] = datetime.now()

    def check_output_response(self, response, allow_repeat=False,
                              add_response=True):
        """Throw Bad_response_error on null responses, and, if not
        allow_repeat, if the response was already output not too long ago.
        Otherwise, set response as last-used response if add_response is True,
        and return response list, split by newlines."""
        
        if not [line for line in response if response.strip()]:
            raise Bad_response_error
        if not allow_repeat:
            try:
                if (datetime.now() -
                    self.last_replies[response.lower()] <
                        PATTERN_RESPONSE_RECYCLE_TIME):
                    raise Bad_response_error
                elif add_response:
                    self.add_last_reply(response)
            except KeyError:
                if add_response:
                    self.add_last_reply(response)

        self.last_reply = response
        return response.split('\n')
    
    def clean_up_last_replies(self):
        """Remove stale (no longer applicable) entries from self.last_replies
        dictionary"""
        num_removed = 0
        orig_size = len(self.last_replies)
        for k, d in self.last_replies.items():
            if (datetime.now() - d > PATTERN_RESPONSE_RECYCLE_TIME):
                print(
                    "clean_up_last_replies: "
                    "Removed stale last_replies entry {} ({})".format(
                        repr(k), d)
                )
                del self.last_replies[k]
                num_removed += 1
        print(
            "clean_up_last_replies: "
            "Removed {} items (len {} -> {})".format(
                num_removed, orig_size, len(self.last_replies))
        )

    def nikkysim_remark(self, msg='', strip_number=True):
        """Generate a NikkySim remark.  If not strip_number, include the
        saying number before the remark."""

        out, self.last_nikkysim_saying = nikkysim(strip_number)
        return out

    def generic_remark(self, msg=''):
        """Select a random remark from the predefined random remark list"""
        nick=''
        m = re.match(r'<(.*)>', msg)
        if m:
            nick = m.group(1)
        return choice(GENERIC_REMARKS).format(nick)

    def remark(self, msg='', add_response=True):
        """Choose between a context-less predefined generic remark or a
        NikkySim remark, avoiding repeats in short succession.  Add new
        response to self.last_replies if add_response."""
        for i in xrange(RECURSE_LIMIT):
            try:
                return self.check_output_response(
                    choice((self.nikkysim_remark(), self.generic_remark(msg))),
                    add_response=add_response
                )
            except Bad_response_error:
                pass
        return ['']

    def pattern_reply(self, msg, add_response=True):
        """Generate a reply using predefined pattern/response patterns.
        Check for and avoid repeated responses.  Add new response to
        add_response to self.last_replies if add_response."""
        for i in xrange(RECURSE_LIMIT):
            response, allow_repeat = \
                pattern_reply(msg, self.last_reply, self.nick)
            try:
                return self.check_output_response(
                    response, allow_repeat, add_response=add_response)
            except Bad_response_error:
                pass
        return self.markov_reply(msg)

    def markov_reply(self, msg, add_response=True, _recurse_level=0):
        """Generate a reply using Markov chaining. Check and avoid repeated
        responses.  Add new response to self.last_replies if add_response."""
        if _recurse_level > RECURSE_LIMIT:
            return random_markov()

        # Split speaker nick and rest of message
        m = re.match(r'<(.*?)> (.*)', msg)
        if m:
            sourcenick = m.group(1)
            msg = m.group(2)
        else:
            sourcenick = ''
        if msg.startswith('{}: '.format(self.nick.lower())):
            msg = msg[len(self.nick) + 2:]

        # Transform phrases in input
        for transform in (
                        (r'\b' + re.escape(self.nick) + r'\b', sourcenick,
                            False),
                        (r'\bwhy\b', 'because', False),
                        (r'\bare you\b', 'am I', True),
                        (r'\byou are\b', 'I am', True),
                        (r"\byou're\b", "I'm", True),
                        (r'\bI am\b', 'you are', True),
                        (r'\bI\b', 'you', True),
                        (r'\byou\b', 'I', True),
                        (r'\bme\b', 'you', True)
                        ):
            old, new, stop_here = transform
            new_msg = re.sub(old, new, msg)
            if msg != new_msg:
                msg = new_msg
                if stop_here:
                    break

        out = markov_reply(msg.rstrip()).rstrip()

        # Transform phrases at beginning of reply
        for transform in (
                        # Avoid self-references in third person
                        (self.nick + ' has ', 'I have '),
                        (self.nick + ' is', 'I am'),
                        (self.nick + ':', sourcenick + ': '),
                        ('nikkybot', 'nikky'),
                        ('nikkybot:', sourcenick + ':'),
                        ):
            old, new = transform
            if out.lower().startswith(old):
                out = new + out[len(old):]
                break
        out = out.replace(self.nick, sourcenick)

        # Transform initial highlights to a highlight to the speaker for a
        # sense of realism
        if sourcenick and randint(0, 10):
            out = re.sub(r'\S+: ', sourcenick + ': ', out)

        try:
            return self.check_output_response(out, add_response=add_response)
        except Bad_response_error:
            return self.markov_reply(msg, _recurse_level=_recurse_level+1)

    def reply(self, msg):
        """Generic reply method.  Try to use pattern_reply; if no response
        found, fall back to markov_reply"""

        try:
            out = self.pattern_reply(msg)
        except Dont_know_how_to_respond_error:
            out = self.markov_reply(msg)
        # This function should be guaranteed to give a non-null output
        out_okay = False
        for line in out:
            if line.strip():
                out_okay = True
                break
        assert(out_okay)
        return out

    def decide_remark(self, msg):
        """Determine whether a random response to a line not directed to
        nikkybot should be made"""

        pacific = timezone('US/Pacific')    # Where Nikky lives
        hour = datetime.now(pacific).hour
        i = int(hour >= 2 and hour <= 12)   # 0 = awake; more activity
                                            # 1 = usually asleep; less activity
        try:
            potential_response = self.pattern_reply(msg, add_response=False)
        except Dont_know_how_to_respond_error:
            c = REMARK_CHANCE[2 + i]
            if re.search(r'\bnikky\b', msg, re.I):
                c = int(c/2)
            r = randint(0, c)
            if not r:
                if not randint(0, 4):
                    return self.remark(msg, add_response=True)
                else:
                    for i in xrange(RECURSE_LIMIT):
                        out = self.markov_reply(msg, add_response=False)
                        # Try not to get too talkative with random responses
                        if out.count('\n') <= 2:
                            self.add_last_reply('\n'.join(out))
                            return out
                    return self.remark(msg, add_response=True)
            else:
                return None
        else:
            c = REMARK_CHANCE[0 + i]
            if re.search(r'\bnikky\b', msg, re.I):
                c=int(c/2)
            r = randint(0, c)
            if not r:
                self.add_last_reply('\n'.join(potential_response))
                return potential_response
            else:
                return None

