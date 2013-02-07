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
from os import fstat, stat
import re
import subprocess

from pytz import timezone

import markov


RECURSE_LIMIT = 50


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
                s += i
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
    def __init__(self, string):
        self.chain = string.split(' ')

    def get(self, fmt=None):
        if fmt is None:
            fmt = []
        return markov_forward([x.format(*fmt) for x in self.chain])


class Manual_markov(object):
    """Return a Markov-generated phrase of the given order"""
    def __init__(self, order, text):
        self.order = order
        self.text = text

    def get(self, fmt=None):
        if fmt is None:
            fmt = []
        return manual_markov(self.order, self.text.format(*fmt))


class Recurse(str):
    """Recursively find a response"""
    def get(self, fmt=None, _recurse_level=0):
        if _recurse_level > RECURSE_LIMIT:
            raise Dont_know_how_to_respond_error
        if fmt is None:
            fmt = []
        return pattern_reply(self.format(*fmt))[0]


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
'\001SUCK IT\001',
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

# Basics
(r'\b(hi|hello|hey)\b', 1,
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
        Markov_forward('hi {0}'),
        Markov_forward('hello {0}'),
        Markov_forward('hey {0}'),
        Markov_forward('sup {0}'),
        Markov_forward('shut the')
    )
),
(r"\b(how are you|how's your|how is your)\b", 1,
    R('Super', 'Awesome', 'Better than your face',
        Markov_forward('better than'),
        Markov_forward('better than your'),
        Markov_forward('worse than'),
        Markov_forward('worse than your')
    ),
),
(r"\b(good night|goodnight|g'?night)\b", 1,
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
1,
    R(
        'Bye forever',
        'I hope I never see you again',
        'BYE FOREVER',
        'I HOPE I NEVER SEE YOU AGAIN',
        'Loser',
        "Loser\nWe don't need you anyway",
        'bye lamers',
        'Good riddance',
        Markov_forward('bye {0}')
    )
),
(r"\b(congratulations|congrats)", 1, R('Thanks', 'thx')),
(r'\b(brb|be right back)\b', 1, R('k', 'kk')),
(r'\b(thanks|thank you)\b', 1,
    R(
        Markov_forward("you're welcome"),
        'np'
    )
),
(r'\bno\W*thanks\b', 0, R('DIAF then')),
(r'\b(wb|welcome back|welcoem back)\b', 1, R('Thanks', 'No\nGo away')),
(r"\b\*\*\*yes/no\*\*\*\b", 1,
    R(
        'yes', 'no', 'maybe', 'probably', 'who knows', 'dunno', "don't know",
        'yeah',
        Markov_forward('yes'),
        Markov_forward('no'),
        Markov_forward('maybe'),
        Markov_forward('dunno'),
        Markov_forward('yeah')
    )
),

# General
(r"^(who is|who's|what is|what's|how's|how is) (.*?)\W?$", -1,
    R(Markov_forward('{1} is')),
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
(r"I'm", 1,
    R('Congratulations', 'Uh, congratulations?', 'k', 'nice', "I'm sorry")
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
(r"\b(would you like|want to|you want to|wanna|you wanna) hear\b", 1,
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
(r'\b(bonfire|fire|flames)\b', 1,
    R(
        Recurse('burns'),
        Recurse('flames'),
        Recurse('extinguisher'),
        Recurse('fries')
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
(r'\b(lousy|freaking|stupid|damn|dumb|farking)\b', 1,
    R('sorry', 'sry', 'sorry\n:(')
),
(r'\byou t?here\b', 0,
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
(r'\bcontest\b', 1,
    R(
        Recurse("You'll lose"),
        Recurse('My entry'),
        Markov_forward('Contests')
    )
),
(r'\b(fever|cold|sick|ill|vomit|throw up|mucus|infection|injury|under the weather|a cold)\b', 1,
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
(r'\bdisallowed word\b', 1,
    R(
        'Shut up {0}',
        'SHUT UP {0}',
        Markov_forward('shut up {0}'),
        Markov_forward('shut up'),
        Recurse('censorship'),
        Recurse('censoring'),
        Recurse('censoring tardmuffin'),
        Recurse('tardmuffin'),
        Recurse('saxjax'),
        'This channel sucks\ntoo much censorship'
    )
),
(r'\brules\b', 1, R("\001ACTION rules {0}\001")),
(r'\b(how much|how many|what amount)\b', -1,
    R(
        Markov_forward('enough'),
        Markov_forward('too many'),
        Markov_forward('more than you')
    )
),
(r'\btroll', 0,
    R('Need a troll fix?\nTry TrollMix(TM)\nbrought to you by yours truly')
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
(r'(Do )?you like (.*)(.*?)\W?$', 0,
    R(
        Recurse('what do you think about {2}'),
        Recurse('yes'),
        "no\nworst thing in the world",
        'no\nit sucks',
        'of course'
    )
),
(r'\b(who (made|wrote|programmed) you|(who\'s|whose) are you)\b', -1,
    R('tev')
),
(r"\bthat ((made|makes|is making) no sense|does not .* make (any |no )?sense|doesn't .* make (any |no )?sense|.* sense make)\b", 1,
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
(r'\b(nicky|niccy|nicci|nikki)\b', 0, R('Who the hell is "{1}"?')),
(r'\b(you|nikkybot) did\b', 1,
    R('I did?', 'I what?', 'Someone talking about me?')
),
(r'\b(you|nikkybot) does\b', 1,
    R('I do?', 'I what?', 'Someone talking about me?')
),
(r'\byou are (a |an |)\b(.*)\b', 1,
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
(r'\b(are you|is nikkybot) (a |an )\b(.*)\b', 1,
    R(
        'yes',
        'no',
        'maybe',
        'dunno',
        'Are *you* {1}{2}?',
        'Describe exactly what you mean by {2}',
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
(r"^(what do you think|how do you feel|(what is|what's|what are) your (thought|thoughts|opinion|opinions|idea|ideas)) (about |of |on )(a |the |an )?(.*?)\W?$", -3,
    R(Markov_forward('{6}'))
),
(r"^(how is|how's|do you like|you like) (.*?)\W?$", -3,
    Recurse('what do you think of {2}')
),

# Memes
(r'\b(fail|epic fail)\b', 1, R('Yeah, you suck', 'HAW HAW', 'Lame')),
(r'\<3 (.*)', 1, R('{0} loves {1}')),
(r'\o/', 1, R('\o/')),
(r'$\>.*', 1, R('>true dat', '>hi kerm\n>is\n>this\n>annoying?')),

# Cemetech
(r'\bCemetech\b', 1,
    R('Cemetech sucks', 'Cemetech\nmore like\nOmnimaga', 'Kammytech sucks')
),
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
(r'\bdelete.*\bpost\b', 1,
    R(
        'CENSORSHIP',
        Recurse('censorship'),
        Recurse('disallowed word')
    )
),
(r'\*(\S+) deleted a post in', 1,
    R('CENSORSHIP', 'Censorship', '{1} YOU CENSORING TARDMUFFIN')
),
(r'\bspam post', 1, R("Don't care", "\001ACTION spams {0}\001")),
(r'\b\*\*\*decbot karma\*\*\*\b', 1,
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
        Markov_forward('thanks {0}'),
        'Thanks {0}\n<3',
        '{0}++',
        'karma sucks',
        'Decbot sucks',
        'Decbot3 sucks',
        'Decbot sucks\nDecbot3--',
        'yourmom++',
        'yourface++',
        Recurse('***decbot karma***')
    )
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
        Recurse('what do you think of {0}'),
        Recurse('what do you think of {1}')
    )
),

# Programming
(r'\b(BASIC|C\+\+|C#|C\s|Java|Javascript|Lua|\s\.NET\s|Ruby|TCL|TI\-BASIC|TI BASIC|Python|PHP|Scheme)', 2,
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
(r'\b(what command|which command|what do I enter|what should I enter|what do I type|what should I type)\b', 1,
    R(
        Markov_forward('sudo'),
        Markov_forward('chown'),
        Markov_forward('rm'),
        Markov_forward('format'),
        Markov_forward('kill'),
        Markov_forward('select'),
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
(r'\b(random (quote|saying)|nikkysim)\b', 1,
    E('nikkysim(stripNumber=False)[0]')
),
(r'\b(tell|tell us|tell me|say) (something|anything) (.*)(smart|intelligent|funny|interesting|cool|awesome|bright|thoughtful|entertaining|amusing|exciting|confusing|sensical|inspiring|random|wise)\b', 1,
    E('choice(["","","","","","Okay\\n","k\\n","kk\\n","Fine\\n"])+nikkysim(stripNumber=True)[0]')
),
(r'#([A-Za-z]-)?([0-9]+)(-([0-9]+))?', -2,
    E('nikkysim_parse_saying_no("{1}", "{2}", "{3}")'),
True),
(r'\brandom number\b', 0,
    R(
        E('randint(0,9999)'),
        E('randint(0,999999999999)'),
        E('str(randint(0,int(\'9\'*100))) + "\\nLong enough for you?"')
    )
),
(r'^markov5 (.*)', -99, Manual_markov(5, '{1}')),
(r'^markov4 (.*)', -99, Manual_markov(4, '{1}')),
(r'^markov3 (.*)', -99, Manual_markov(3, '{1}')),
(r'^markov2 (.*)', -99, Manual_markov(2, '{1}')),
)

# === END OF DATA SECTION =====================================================


class Nikky_error(Exception):
    pass

class Dont_know_how_to_respond_error(Nikky_error):
    pass

class Repeated_response_error(Nikky_error):
    pass


def nikkysim(stripNumber=True, saying=None):
    if saying is None:
        x, y = randint(0, 4294967295), randint(0, 9999)
    else:
        x, y = saying
    out = subprocess.check_output(['nikky', '{}-{}'.format(x, y)])
    if stripNumber:
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
f5 = open('nikky-markov.5.pickle', 'rb')
markov5 = cPickle.load(f5)
f4 = open('nikky-markov.4.pickle', 'rb')
markov4 = cPickle.load(f4)
f3 = open('nikky-markov.3.pickle', 'rb')
markov3 = cPickle.load(f3)
f2 = open('nikky-markov.2.pickle', 'rb')
markov2 = cPickle.load(f2)
last_mtime = (fstat(f2.fileno()).st_mtime, fstat(f3.fileno()).st_mtime,
    fstat(f4.fileno()).st_mtime, fstat(f5.fileno()).st_mtime)
f5.close()
f4.close()
f3.close()
f2.close()
markovs = {5: markov5, 4: markov4, 3: markov3, 2: markov2}


def markov_pickles_changed():
    new_mtime = (stat('nikky-markov.2.pickle').st_mtime,
        stat('nikky-markov.3.pickle').st_mtime,
        stat('nikky-markov.4.pickle').st_mtime,
        stat('nikky-markov.5.pickle').st_mtime,)
    return new_mtime != last_mtime


def memory_cleanup():
    """Workaround to allow avoiding excessive memory consumption when
    reloading module (these variables can consume an enormous amount)"""
    global markovs, markov2, markov3, markov4, markov5
    try:
        del markovs, markov2, markov3, markov4, markov5
    except:
        pass


def markov_reply(msg):
    words = msg.split()
    for order in (5, 4, 3, 2):
        availReplies = []
        for i in range(len(words)):
            response = \
                markovs[order].sentence_from_chain(tuple(words[i:i+order]))
            if response:
                availReplies.append(response)
        if availReplies:
            return choice(availReplies)
    words.sort(key=len)
    words.reverse()
    for word in words:
        response = markov5.sentence_from_word(word)
        if response:
            return response
    return markov5.sentence_from_chain(choice(tuple(markov5.chain_forward.keys())))
    ### FIXME: Handle empty replies ###
    ### TODO: Experiment with priorities (choosing response based on length, etc.) ###


def manual_markov(order, msg):
    m = markovs[order]
    chain = tuple(msg.split())
    if len(chain) == 1:
        response = m.sentence_from_word(chain[0])
    else:
        response = m.sentence_from_chain(chain)
    if response:
        return response
    return '"{}": chain not found'.format(' '.join(chain))
    ### TODO: Try harder to find a chain if not found initially


def markov_forward(chain):
    """Generate sentence from the current chain forward only and not
    backward"""

    if len(chain) == 1:
        m = choice(markovs.values())
        return ' '.join(m.from_word_forward(chain[0])).replace(' \n ', '\n')
    else:
        m = markovs[len(chain)]
        return ' '.join(m.from_chain_forward(chain)).replace(' \n ', '\n')


def pattern_reply(msg, last_used_reply='', nick='nikkybot'):
    # Separate out speaker's nick if known
    m = re.match(r'<(.*?)> (.*)', msg)
    if m:
        sourcenick = m.group(1)
        msg = m.group(2)
    else:
        sourcenick = ''

    # Remove highlight at beginning of line, if it exists
    m = re.match(re.escape(nick) + r'\W *(.*)', msg)
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
            print('Regex: {}'.format(pattern))
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
        raise Dont_know_how_to_respond_error
    fmt_list = (sourcenick,) + match.groups()
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

    def check_output_response(self, response, allow_repeat=False):
        """If not allow_repeat, check if the response was already output
        not too long ago; do exception if so, else record when this response
        was last used.  Also set response as last-used response if accepted.
        If accepted, return response list, split by newlines."""

        if not allow_repeat:
            try:
                if (datetime.now() -
                    self.last_replies[response.lower()] <
                        PATTERN_RESPONSE_RECYCLE_TIME):
                    raise Repeated_response_error
            except KeyError:
                self.last_replies[response.lower()] = datetime.now()

        self.last_reply = response
        return response.split('\n')

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

    def remark(self, msg=''):
        """Choose between a context-less predefined generic remark or a
        NikkySim remark, avoiding repeats in short succession"""
        for i in xrange(RECURSE_LIMIT):
            try:
                return self.check_output_response(choice(
                    (self.nikkysim_remark(), self.generic_remark(msg))))
            except Repeated_response_error:
                pass
        return ['']

    def pattern_reply(self, msg):
        """Generate a reply using predefined pattern/response patterns.
        Check for and avoids repeated responses."""
        for i in xrange(RECURSE_LIMIT):
            response, allow_repeat = \
                pattern_reply(msg, self.last_reply, self.nick)
            try:
                return self.check_output_response(response, allow_repeat)
            except Repeated_response_error:
                pass
        return self.markov_reply(msg)

    def markov_reply(self, msg, _recurse_level=0):
        """Generate a reply using Markov chaining. Check and avoid repeated
        responses."""
        if _recurse_level > RECURSE_LIMIT:
            # FIXME: Output a random Markov response
            return markov_reply('')

        # Split speaker nick and rest of message
        m = re.match(r'<(.*?)> (.*)', msg)
        if m:
            sourcenick = m.group(1)
            msg = m.group(2)
        else:
            sourcenick = ''

        # Avoid referring to self in third person
        msg = msg.replace(self.nick, sourcenick, 1)
        out = markov_reply(msg).rstrip()
        for transform in ((self.nick + ' has ', 'I have '),
                        (self.nick + ' is', 'I am'),
                        (self.nick + ':', sourcenick + ': '),
                        ):
            old, new = transform
            if out.lower().startswith(old):
                out = new + out[len(old):]
                break
        out = out.replace(self.nick, sourcenick)

        # TODO: More transformations? (you <-> I, why -> because, etc.)

        # Occasionally highlight the speaker back for a sense of realism
        if sourcenick and randint(0, 10):
            out = re.sub(r'\S+: ', sourcenick + ': ', out)
        try:
            return self.check_output_response(out)
        except Repeated_response_error:
            return self.markov_reply(msg, _recurse_level + 1)

    def reply(self, msg):
        """Generic reply method.  Try to use pattern_reply; if no response
        found, fall back to markov_reply"""

        try:
            return self.pattern_reply(msg)
        except Dont_know_how_to_respond_error:
            return self.markov_reply(msg)

    def decide_remark(self, msg):
        """Determine whether a random response to a line not directed to
        nikkybot should be made"""

        pacific = timezone('US/Pacific')    # Where Nikky lives
        hour = datetime.now(pacific).hour
        i = int(hour >= 2 and hour <= 12)   # 0 = awake; more activity
                                            # 1 = usually asleep; less activity
        try:
            potential_response = self.pattern_reply(msg)
        except Dont_know_how_to_respond_error:
            c = REMARK_CHANCE[2 + i]
            if re.search(r'\bnikky\b', msg, re.I):
                c = int(c/2)
            r = randint(0, c)
            if not r:
                return choice((self.remark(msg),)*5 + (self.markov_reply(msg),))
            else:
                return None
        else:
            c = REMARK_CHANCE[0 + i]
            if re.search(r'\bnikky\b', msg, re.I):
                c=int(c/2)
            r = randint(0, c)
            if not r:
                return potential_response
            else:
                return None

