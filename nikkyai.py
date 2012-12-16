#!/usr/bin/env python3

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

# TODO:
#   - Recurse() doesn't appear to be working properly
#   - Randomly fails to honor priority settings and choose the wrong regex?
#   - Getting messy; probably need some major refactoring

from datetime import datetime, timedelta
from random import randint, choice
import pickle
import re
import subprocess

from pytz import timezone

import markov

#For debugging
from imp import reload
reload(markov)

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
            return i
            
            
class E(str):
    """Evaluate string"""
    def __init__(self, *args):
        self.msg = ''
        self.match = None
        str.__init__(self)
    
    def get(self, fmt=None):
        if fmt is None:
            fmt = []
        return str(eval(self.format(*fmt)))


class Recurse(str):
    pass


# === DATA SECTION ============================================================

# (has pattern response & awake, has pattern response & asleep,
#  random remark & awake, random remark & asleep)
REMARK_CHANCE = (200, 800, 700, 2100)
PATTERN_RESPONSE_RECYCLE_TIME = timedelta(7)

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
# pattern regexp, priority, action

# Basics
(r'\b(hi|hello|hey)\b', 1, R(S(R('Sup ', "What's up "), R('homies', 'losers', 'whores', 'G', 'hookers')), 'Suppppppppp', "Shut up", "Flood your face!", "FLOOD YOUR FACE", 'HI {0}', 'Go away', 'No\ngo away')),
(r"\b(how are you|how's your|how is your)\b", 1, R('Super', 'Awesome', 'Better than your face')),
(r"\b(good night|goodnight|g'?night)\b", 1, R('Sweet dreams.\nBitch', 'night', "Good night\nluckily I don't sleep", "Haw haw\nI never need to sleep\nsleep is for losers", "night\nluckily I don't need sleep")),
(r'\b(bed|sleep|tired)\b', 1, R("I don't sleep", 'sleep is for losers')),
(r"\b(bye|bye bye|goodbye|good bye|see you later|night|good night|g'night)\b", 1, R('Bye forever', 'I hope I never see you again', 'BYE FOREVER', 'I HOPE I NEVER SEE YOU AGAIN', 'Loser', "Loser\nWe don't need you anyway", 'bye lamers', 'Good riddance')),
(r"\b(congratulations|congrats)", 1, R('Thanks', 'thx')),
(r"\b((good |g'?)(morning|evening|afternoon)|^(morning|evening|afternoon))", 1, S('Good ', R('morning', 'evening', 'afternoon', 'riddance'), ' to you too', R('', ', {0}'))),
(r'\b(brb|be right back)\b', 1, R('k', 'kk')),
(r'\b(thanks|thank you)\b', 1, R(S("You're welcome", R(' snookie bear', '')), 'np')),
(r'\bno\W*thanks\b', 0, R('DIAF then')),
(r'\b(wb|welcome back|welcoem back)\b', 1, R('Thanks', 'No\nGo away')),
(r'\bwelcome\b', 1, R('welcome to shut up')),

# General
(r"^(who is|who's|what is|what's|how's|how is) (.*?)\W?$", -1, E('markovReply(""" {2} is a """)')),
(r'\b(cares|care)\b', 1, R('No, nobody cares')),
(r'\b(what|who) (is|are)\b', 1, R('Your mom', 'Your face', 'Me')),
(r'\bwho\b', 0, R('Nobody', "nobody\nthat's who", 'NOBODY', "NOBODY\nTHAT'S WHO", 'me')),
(r'\b(you suck|your .* sucks)\b', 1, R(':(', 'So does your face', 'So does your mom', 'Die', 'DIAF', 'STFU', 'Suck it', 'Suck it dry', ':(', ':(\nDo I suck?')),
(r'.* (suck|sucks)', 2, R("Don't be hatin'", 'k', 'kk')),
(r'\bi suck\b', 1, R(':(')),
(r'\bsuck (a |an )\b(.*)\b', 1, R('k', 'kk', 'kk\n\001ACTION sucks {1}{2}\001')),
(r'\bShut up\b', 1, R('I hate you', 'k', 'kk')),
(r"\b(do not|don't) (really )?care\b", 1, R("Yeah, I don't care either.")),
(r"\bright\b", 1, R('Wrong.', 'yes')),
(r"\b(i .* wish|wish i)\b", 1, R('Me too')),
(r"\bfollowed us\b", 1, R("False. I've been here for two years.")),
(r"^good$", 1, R('Great!', 'Great')),
(r"\bwhat's up with you\b", 1, S(R("I'm just doing what I was told\nSO SUCK IT DRY"), R('', '\nsaniojfklsjfklsd;jskdl;jasdklajirsljraie;jriaserl;'))),
(r"\bwhat's up with\b", 2, R('It hates you')),
(r"\bmy.*\b((blog|book|calc|calculator|channel|program|prog|website|site|bot)s)", 1, S('Your {1} suck\n', R('No one will like them', 'Can you give me a link so I can further make fun of them?', ''))),
(r"\bmy.*\b(blog|book|calc|calculator|channel|program|prog|website|site|bot)\b", 2, S('Your {1} sucks\n', R('', 'No one will like it', 'Can you give me a link so I can further make fun of it?'))),
(r"\b(some|these|those)\b.*\b((blog|book|calc|calculator|channel|program|prog|website|site|bot)s)\b", 1, S('Those {2} suck\n', R('', 'No one will like them', 'Can you give me a link so I can further make fun of them?'))),
(r"\b(a|an|the|this|that)\b.*\b(blog|book|calc|calculator|channel|program|prog|website|site|bot)\b", 2, S('That {2} sucks\n', R('', 'No one will like it', 'Can you give me a link so I can further make fun of it?'))),
(r"(\w+)('s)\b.*?\b((blog|book|calc|calculator|channel|program|prog|website|site|bot)s)\b", 1, S('{1}{2} {3} suck\n', R('', 'No one will like them', 'Can you give me a link so I can further make fun of them?'))),
(r"(\w+)('s)\b.*?\b(blog|book|calc|calculator|channel|program|prog|website|site|bot)\b", 2, S('{1}{2} {3} sucks\n', R('', 'No one will like it', 'Can you give me a link so I can further make fun of it?'))),
(r'^(kerm|kermm)\b', 1, R(S('KERMM KERMM KERMM KERMM\nSomeone needs you', R('', '\nGET IN HERE NOW')), "Don't bother\nKermM is too lame", "Kerm sucks\nDon't waste your time")),
(r"I'm", 1, R('Congratulations', 'Uh, congratulations?', 'k', 'nice', "I'm sorry")),
(r'\bdiaf\b', 1, R('\001ACTION burns\001', S('\001ACTION lights himself on fire\001', R('','\n\001ACTION burns\001')), 'kk')),
(r'\b(gun|guns)\b', 1, R('Just ban all guns. Problem solved.')),
(r'\bnew xkcd\b', 1, R("Don't care.\nXKCD isn't funny.\nSorry to say.")),
(r'\bnew\b', 1, R("Don't care.")),
(r"\b(i am|i'm) bored\b", 1, R('Write a new OS.')),
(r"\b(yes|yeah|no|is .* true)\b", 2, R('Yes', 'Yeah?', 'No', 'Not a chance')),
(r"$(yes|yeah|no|is.* true)\b", 2, R(Recurse('yes'), 'Oh\nWell DIAF then', 'k', 'kk')),
(r"\b(would you like|want to|you want to|wanna|you wanna) hear\b", 1, R("Yes, please bore us to death.")),
(r'\byou need to\b', 1, R('You need to suck it.')),
(r'\bi need to\b', 1, R('You also need to shut up', 'You also need to suck it')),
(r"\b(should i|let'?s)\b", 1, R('Yes, you should', 'DO IT')),
(r'\bwho am i\b', -1, R('You are {0}', E('markovReply("You are")'))),
(r'\butc\b', 1, R('UTC is pretty great')),
(r'\bi will\b', 1, R('Good, go do it', 'k', 'thanks')),
(r'\b(music|instrument)', 1, R('Music sucks\nOnly losers play instruments')),
(r'\bbacon\b', 1, R('Bacon is gross')),
(r'\breboot\b', 1, R('\001ACTION reboots {0}\001\nlolrotflrebooted')),
(r'\bi am\b', 1, R('yes you are')),
(r'\byes,? i do\b', 1, R('me too')),
(r'\banything interesting\b', 1, R('no')),
(r'\b(anyone|you) around\b', 1, R('yes', 'hi')),
(r'\bso do(es)?\b', 1, R('so does your face', 'so does your mom', 'so do you', 'so do I')),
(r'\bsounds like fun\b', 1, R('sure is', 'nope')),
(r"\b(what's up|what are you (up to|doing))\b", 1, R('studying', 'studying\nhow to be a human', 'studying\ncomparitive law')),
(r'\byour mom\b', 1, R(':(')),
(r'\b(beer|booze|drink|drunk|wine|vodka)\b', 1, R('BOOZE')),
(r'\bI hate\b', 1, R('I hate you too', ':(\nI hate you too', 'I HATE YOU {0}\nNerd')),
(r'\bemails\b', 1, R("Hahaha\nI'm sure it's all spam")),
(r"\bis(n't)?\b.*\?", 1, R('yes', 'no', 'maybe')),
(r'\bsets\b.*\bon fire\b', 1, R('\001ACTION burns\001')),
(r"\byou're a loser\b", 0, R('yes')),
(r'\b(borking|bork|borked)\b', 1, R('{1}?\nlike Judge Bork?')),
(r'\bcall (me|them|him|her|it|yourself|himself|herself|itself|myself)\b', 1, R("Or I'mstupid")),
(r'\bwhere.*you hear that\b', 1, R('Omnimaga', 'your mom', 'your face')),
(r'\b(why|how come)\b', 0, R("because you're wrong", "because you don't", "because you do", 'because you suck', 'because your mom sucks', 'because your face sucks', 'Why not?', 'Because I give a hoot')),
(r'\b(lousy|freaking|stupid|damn|dumb|farking)\b', 1, R('sorry', 'sry', 'sorry\n:(')),
(r'\byou t?here\b', 0, R('no', "No\nhe said he's never talking to anyone again", 'no', 'no\ngo away', 'Shut up')),
(r'\bfeel old\b', 1, R('old fart')),
(r'\b(plz|please) ignore\b', 1, R("kk\nI'll ignore you forever", 'k\n\001ACTION puts {0} on permanent ignore\001')),
(r'\b(oops|oops|whoops|oopsie|oppsie)\b', 1, R('HAHAHAHAHA\nFAIL')),
(r'\bi hate\b', 1, R("Don't use it", "Don't use it\nProblem solved!", 'me too', 'I hate it too', "Don't use it\nI hate it too")),
(r'\bwhat does it mean\b', 1, R('Communism.')),
(r"\bmy \S*('s| is) better than yours", 1, R("I\nam\nsure it is")),
(r'\bcontest\b', 1, R("You'll lose.\nMy entry is far superior.", 'Contests are stupid.', 'Contests suck')),
(r'\b(fever|cold|sick|ill|vomit|throw up|mucus|infection|injury|under the weather|a cold)\b', 1, R('I HOPE YOU STAY SICK FOREVER', 'Will a hug make it better?')),
(r'\bfault\b', 1, S("No, it's your ", R("mom's", "face's"), " fault")),
(r"\bi don't feel like\b", 1, R('lazy', "I don't feel like reading what you write", 'me neither', ':(', 'DO IT ANYWAY')),
(r'\bscribble\b', 1, R('\001ACTION scribbles on {0}\001')),
(r'\bbiased against me\b', 1, R('Yeah\ncause you suck')),
(r'\bdisallowed word\b', 0, R('Shut up {0}', 'SHUT UP {0}', 'This channel sucks\ntoo much censorship', '{0} YOU STUPID CENSORING PIECE OF CRAP', 'Suck it {0}', 'SHUT UP {0}\nCENSORING TARDMUFFIN PIECE OF SHIT')),
(r'\bstatus nick\b', 1, R("And I won't hesitate to squat your nick if you use a status nick")),
(r'\brules\b', 1, R("\001ACTION rules {0}\001")),
(r'\b(how much|how many|what amount)\b', -1, R(E("' '.join(markov5.from_word_forward('Enough'))") ,E("' '.join(markov3.from_chain_forward(('Too','many')))"), E("' '.join(markov3.from_chain_forward(('More','than','you')))"))),

# Meta
(r'\b((how much|how many lines (of)?|how much) (code|coding|programming)|how long .* to (make|program|code|design|write) you)', -2, R(E('subprocess.check_output(["sh", "/home/nikkybot/bot/codecount.sh"]).decode()'), S("About ", E('str((datetime.now() - datetime(2012, 10, 30)).days)'), " days' worth ongoing so far, give or take"), 'About a billion lines of Perl', 'I started out as lines of Perl\nbut then tev had to be a tard and convert it all to Python')),
(r'(Do )?you like (.*)(.*?)\W?$', 0, R(Recurse('what do you think about {2}'), Recurse('yes'), "no\nworst thing in the world", 'no\nit sucks', 'of course')),
(r'\byou hate\b', 0, R(Recurse('yes'), 'with a passion')),
(r'\b(learn|teach)', 1, R("I learned something new today!", 'I learn something new every day!', 'tev and nikky teach me everything I know', "tev and nikky teach me everything I know")),
(r'\b(who (made|wrote|programmed) you|(who\'s|whose) are you)\b', -1, R('tev')),
(r"\bthat ((made|makes|is making) no sense|does not .* make (any |no )?sense|doesn't .* make (any |no )?sense|.* sense make)\b", 1, R('Sorry', 'sorry\n:(', 'Well, blame tev', 'Neither do you\nEnglish sucks', 'I wish I could do better\n*sob*')),
(r'\bhuman\b', 1, R('My aim in life is to be human')),
(r"\b(we have|there is|there's|it's|a) ?(\ba\b )?nikkybot\b", 1, R("I'm filling in for the real nikky", 'Yes', 'duh', 'Yes\nnikky is too busy trolling elsewhere\ner, I mean conducting constructive discussion', 'hi')),
(r"\bcue (nikky's |nikkybot's |nikky |nikkybot )?[\"']?([^\"']*)[\"']?", -1, R('{2}')),
(r'\b(nicky|niccy|nicci|nikki)\b', 0, R('Who the hell is "{1}"?')),
(r'\b(nikky\w*|you) (are|is) not allowed\b', 1, R("It's true\nI'm not")),
(r'\bnikky\b\W*(\bnikky\b)+', 0, R('NIKKY NIKKY NIKKY NIKKY NIKKY NIKKY NIKKY', 'NIKKY NIKKY NIKKY NIKKY NIKKY NIKKY NIKKY MUSHROOM MUSHROOM', 'nikky nikky nikky nikky nikky nikky nikky nikky nikky\nmushroom MUSHROOM')),
(r'\bnikky\b', 0, R('nikky rules', 'nikky <3', 'nikky is so awesome\nI want to be just like him', 'nikky is my role model')),
(r'\b(you|nikkybot) did\b', 1, R('I did?', 'I what?', 'Someone talking about me?')),
(r'\b(you|nikkybot) does\b', 1, R('I do?', 'I what?', 'Someone talking about me?')),
(r'\b(you|nikkybot) is (a |an |)\b(.*)\b', 1, R("That's what you think", "Yes, I'm totally {1}{2}", 'Am not', 'Why thank you pumpkin', 'Thanks', 'Damn straight', 'Where did you hear that?')),
(r'\b(are you|is nikkybot) (a |an )\b(.*)\b', 1, R('yes', 'no', 'maybe', 'dunno', 'Are *you* {1}{2}?', 'Describe exactly what you mean by {2}')),
(r'\b(are you|is nikkybot) a troll\b', 1, R('depends on the weather', 'No, I care about everyone', 'No, I love everyone\nexcept you')),
(r'\b(are you|is nikkybot) (borked|b0rked|broken|screwed|messed|fucked)\b', 1, R("yes\nWell, no\nbut tev's code is", 'about as much as my program code', "No\nyou're just incompatible")),
(r'\b((ask|tell) nikky .*)\b', 0, R('HEY NIKKY NIKKY NIKKY\n{0} says "{1}"')),
(r'\bdid you\b', 1, R("I don't remember", "Can't say", 'yes', 'with much gusto!')),
(r"\byour (a|an|my|his|her|its|it's|dumb|stupid)\b", 1, R('"Your" retarded', "*You're")),
(r"\b(you are|you're|nikkybot is)\b", 1, R("I'm actually a very passive person.", "I'm a troll", 'no u', 'yes', 'no', 'of course', 'What can I say?')),
(r"\b(you are|you're|nikkybot is)\b", 1, R("I'm actually a very passive person.", "I'm a troll", 'no u', 'yes', 'no', 'of course', 'What can I say?')),
(r"\b(was|wasn't|was not|was never)*anti", 1, R('I am')),
(r'\bsorry\b', 1, R('you should be')),
(r'\btokens\b', 1, R("No, we're not featuring Tokens.\nHar har har")),
(r'^(what do you think|how do you feel) (about|of) (a |the |an )?(.*?)\W?$', -1,
E('" ".join(markov3.from_word_forward("""{4}"""))')),

# Generic Nikky phrases
(r'\b(Arch Linux|Arch|email|the internet|Dell|iPhone|Nspire|Omnimaga|Ubuntu|X\b|Xorg|basic|TI.?BASIC|Blackberry|censorship|communism|dialup|drama|KDE|Linux|Lunix|Mac|OS X\b|Palm|PC|Pentium|Pokemon|Pokémon|Prizm|rickrolling|spelling|(TI.?)?(81|82|83\+|83 Plus|83|84\+|84|84 Plus|85|86|89|Voyage 200|V200|92\+|92 Plus|92)\s?(Titanium|SE)?|eyecandy|malware|Omnidrama|Casio|HP|Emacs|Word\b|pico|nano|vi|vim|GIMP|Photoshop|Paint|MS Paint|Windows|Winblows|Window\$|C#|C\+\+|C\s|Perl|TCL|Java|Javascript|Ruby|Lua|\s\.NET\s|PHP|Python|Apple|LaTeX|Emacs|United TI|UTI|Firefox|Thunderbird|Britain|Evolution|Pine|slypheeed|IE|Opera|Doctor Who|Stargate|MySpace|Kofler|Kevin Kofler|regex|regexp|sc2|sourcecoder|jstified|Scheme|dcs|doorscs|doors cs|being productive|productivity|efnet|irc|digg|punctuation|decbot|decbot2|sax|irc|Tokens)', 2, R('{1} sucks', '{1} rules', '{1} is awesome', '{1} sucks balls', 'Gotta love {}', '{1} <3', "Don't use {1}", '{1} seriously is horrible.', '{1} is too complicated.', 'lol {1}', 'lol {1}\n{0} fails', '{1} ftl', '{1} sucks penis', 'Haha fail\n{1}tard', 'Your face is {1}', 'Your mom is {1}', '{1} kicks ass', '{1} is the downfall of society', '{0}: {1}tard', '<3 {1}', '{1} is blah', '{1} is for losers', E("do_markov4('{1}')"))),
(r'\b(EEEPCs|iPhones|Blackberries|calculators|closed formats|communism|free formats|guns|laptops|memes|notebooks|Palms|PCs|Pentiums|Pokemon|Pokémon|Prizms|quadratic solvers|rickrolls|semicolons|spelling|TI-81s|TI-82s|TI-83s|TI-85s|TI-86s|TI-89s|Voyage 200s|V200s|TI-92s|Windows phones|Winphones|wikis|Casios|HPs|Linux users|regexes|regular expressions|question marks|exclamation points|interrobangs|periods|semicolons|commas|quotes|quotation marks|progress bars)\b', 2, R('{1} suck', '{1} rule', '{1} are awesome', '{1} suck balls', '{1} fail', '{1} kick ass', '{1} are the downfall of society', '{1} are for losers', '{1} are for losers\nGuess who has {1}?\n<-- this champ', '<3 {1}')),

# Memes
(r'\b(fail|epic fail)\b', 1, R('Yeah, you suck', 'HAW HAW', 'Lame')),
(r'\<3 (.*)', 1, R('{0} loves {1}')),
(r'\o/', 1, R('\o/')),
(r'$\>.*', 1, R('>true dat')),

# Calculators
(r'\b(for|for( the)?|(port|ports|porting|ported).*to( the)?|on( the)?) (Nspire|TI-83|TI-83 Plus|TI-83\+|TI-84\+|TI-84 Plus|TI-89|Prizm|Casio Prizm)\b', 1, R("Don't care\n{5} sucks")),
(r'\basm in 28\b', 1, R('it sucks\ntry #tiasm instead')),
(r'\b(calc|calculator)', 1, R('calculators sucks\n[sic]')),

# Cemetech
(r'\bCemetech\b', 1, R('Cemetech sucks', 'Cemetech\nmore like\nOmnimaga', 'Kammytech sucks')),
(r'\b#cemetech\b', 1, R('Join #tcpa', '#cemetech sucks', 'You should join #tcpa\nloser', '#cemetech sucks\njoin #tcpa or #ti', 'Join #tcpa\nYou know you want to', 'Join #ti\nYou know you want to')),
(r'\bdelete.*\bpost\b', 1, R('CENSORSHIP')),
(r'\*(\S+) deleted a post in', 1, R('CENSORSHIP', 'Censorship', '{1} YOU CENSORING TARDMUFFIN')),
(r'\bspam post', 1, R("Don't care", "\001ACTION spams {0}\001")),
(r'\b(karma|decbot|decbot2)\b', 1, R('karma sucks', '!karma SET KARMA = 0 WHERE `user` = "{0}"; DROP DATABASE', 'Decbot sucks', 'Decbot2 sucks', 'Decbot sucks\nDecbot2--', '!karma your face', '!karma your mom')),
(r'nikkybot\+\+', 0, R('Thanks', 'Thanks {0}', 'Thanks {0}\n<3', '{0}++', 'karma sucks', 'Decbot sucks', 'Decbot2 sucks', 'Decbot sucks\nDecbot2--', 'yourmom++', 'yourface++')),
(r'\b(.*)\+\+', 1, R('{0}++', '{0}--', '{0}--\nTake THAT', '{0}--\nHAHAHAHAHAHA ROLFILIL', '{1}++', '{1}--', '{1} sucks', '{1} is awesome', '{1} kicks ass', '{1} sucks balls', 'karma sucks', '!karma SET KARMA = 0 WHERE `user` = "{0}"; DROP DATABASE', '!karma SET KARMA = 0 WHERE `user` = "{1}"; DROP DATABASE', 'Decbot sucks', 'Decbot2 sucks', 'Decbot sucks\nDecbot2--', '{1}++')),


# Omnimaga
(r'\bOmnimaga\b', 1, R('Omnimaga sucks', 'Omnidrama sucks', 'Nobody cares about Omnidrama', "Omnimaga? HAHAHAHAHA, that's hilarious.", 'Omnimaga\nmore like\nLameomaga', 'Omnimaga\nmore like\nomnidrama', 'Omnimaga\nmore like\nwalled garden', 'Omnimaga is the cancer that is killing the community', 'Speaking of Omnimaga\nI just got banned from #omnimaga-spam again\nfor doing nothing but idling!')),

# Programming
(r'\b(BASIC|C\+\+|C#|C\s|Java|Javascript|Lua|\s\.NET\s|Ruby|TCL|TI\-BASIC|TI BASIC|Python|PHP|Scheme)', 2, R('{1} sucks. Should have used Perl.', 'Perl is better', 'Just use Perl', 'Just use Perl\nlike tev *should* have when making me', 'Should have used Perl', 'Perl was my first language', 'Hahahaha\n{1}tard', 'Hahahaha\nWhat a tard')),
(r'\bPHP\b', 1, R('PHP\nmore like\nPrivate Hookers Party', 'PHP sucks', 'Who the hell would use PHP?', 'Let me rant to you for a bit about how terrible PHP is.')),
(r'\bPerl (for a|on a) (calc|calculator|graphing calc|graphing calculator)', 1, R('Yes. Suck it.')),
(r'\bPerl\b', 1, R('Perl\nmore like\nTCL', 'Champ', 'Perl sucks', 'Perl is crap, anyway', 'Perl is crap', 'THE POWER OF PERL COMPELS YOU', 'I love Perl', 'Perl was my first language', 'Wish I was written in Perl\ntev is a wuss')),
(r'\b(which|what) language\b', 1, R('Perl\nDuh')),
(r'\b(which|what) language.*you', 1, R("Python, Bash, and C\nBut I'm secretly plotting to reimplement myself in Perl and delete the old version tev made", "Perl\n...I wish")),
(r'\b(which|what) site\b', 1, R('nvm2u.com', '{0}sucks.org', 'omnimaga.org', 'yourmom.org')),
(r'\bi\b.*\buse(|d|ing)\b.*\bperl\b', 1, R('Good for you', '{0} is such a champ')),

# Computers
(r'\b(what command|which command|what do I enter|what should I enter|what do I type|what should I type)\b', 1, R('sudo rm -rf /', 'rm -rf', 'chown yourmom')),
(r'\b(sudo )?rm \-?rf\b', 1, R('\001ACTION deletes himself\001')),
(r'\bLaTeX\b', 1, R('LaTeX sucks.', 'LaTeX\nsucks', 'LaTeX sucks\nI use vim')),
(r'\bEmacs\b', 1, R('Emacs is designed by a crazy dude, who thinks that all users have 14 arms')),
(r'\bWindows\b', 1, R('lul window$', 'lul winblows', 'Winblows sucks', 'Window$ sucks')),
(r'\bPaint\b', 1, R('Yay, Photoshop!', 'Just use Photoshop')),
(r'\bzombie processes\b', 1, R("Don't use shitnix", "Don't use Linux. Problem solved.")),
(r'\bfailed to (open|save)\b', 1, R('sudo that shit')),
(r'\bOS X\b', 1, R("OS X sucks\nDon't use it, {0}", "OS X sucks\nDon't use it, {0}\nWhat's good about it?\noverpriced\nunderpowered\nand you pay 50% of the cost to Steve Jobs")),
(r'\bshould (use|go back to|go back to using) (MS\-)?DOS\b', 1, R('Sounds like fun to me!')),
(r'\b(macbook pro|mpb)s?\b', 1, R('Macbook Pros suck harder\nunless you like your keys to rub off into rubber blanks\nand paying $1500 a year for a new program')),
(r'\bproprietary\b', 1, R("What's wrong with proprietary?")),
(r'\bmyspace\b', 1, R('{0} loves MySpace')),
(r'[0-9][0-9](\"|inch|\-inch) (3d |3-d )?(lcd|monitor|plasma|crt|dlp)', 1, R('Big monitors are stupid\nnerd')),
(r'\b(monitors|monitor-)', 1, R('anyone with more than one monitor\nis a loser')),
(r'\b(content management system|CMS)\b', 1, R('Your face is a CMS')),
(r"\bfirefox (keeps|doesn't|won't|can't|does not|will not|cannot)\b", 1, R("Don't use shitfox\nproblem solved")),

# ticalc.org
(r'\bticalc(.org)? (news|needs news)\b', 1, R("I'm too busy reviewing Kerm's stupid book.")),

# IRC
(r'\bbetter channel\b', 1, R('A better channel is #omnimaga', 'A better channel is #tcpa', 'A better channel is #cemetech', 'A better channel is #ti', 'A better channel is #calcgames', 'A better channel is #tiasm', 'A better channel is #nspire-lua', 'A better channel is #nspired', 'A better channel is #tcpa', 'A better channel is #prizm', 'A better channel is #hp48', 'A better channel is #omnimagay', 'A better channel is #nikky')),
(r'\b(channel|irc|efnet|chat)\b', 1, R(Recurse('better channel'), 'I was told I should stop by #tcpa')),
(r'\bhighlight\b', 1, R('I like to highlight nikky just to annoy him', 'Hi {0}\nI dare you to highlight everyone in the channel\nin one line')),

# Special functions
(r'\b(random (quote|saying)|nikkysim)\b', 1, E('nikkysim(stripNumber=False)[0]')),
(r'\b(tell|tell us|tell me|say) (something|anything) (.*)(smart|intelligent|funny|interesting|cool|awesome|bright|thoughtful|entertaining|amusing|exciting|confusing|sensical|inspiring|random|wise)\b', 1, E('choice(["","","","","","Okay\\n","k\\n","kk\\n","Fine\\n"])+nikkysim(stripNumber=True)[0]')),
(r'#([A-Za-z]-)?([0-9]+)(-([0-9]+))?', -2, E('nikkysimSayingNo(self.match)')),
(r'\b(qotd|quote of the day)\b', 0, E('"Today\'s quote of the day: " + qotd()')),
(r'\brandom number\b', 0, R(E('randint(0,9999)'), E('randint(0,999999999999)'), E('str(randint(0,int(\'9\'*100))) + "\\nLong enough for you?"'))),
(r'^markov5 (.*)', -99, E('do_markov5(""" {1} """)')),
(r'^markov4 (.*)', -99, E('do_markov4(""" {1} """)')),
(r'^markov3 (.*)', -99, E('do_markov3(""" {1} """)')),
(r'^markov2 (.*)', -99, E('do_markov2(""" {1} """)')),
)

# Markov experiment

f = open('nikky-markov.5.pickle', 'rb')
markov5 = pickle.load(f)
f = open('nikky-markov.4.pickle', 'rb')
markov4 = pickle.load(f)
f = open('nikky-markov.3.pickle', 'rb')
markov3 = pickle.load(f)
f = open('nikky-markov.2.pickle', 'rb')
markov2 = pickle.load(f)
f.close()

# === END OF DATA SECTION =====================================================
    
class NikkyError(Exception):
    pass


class DontKnowHowToRespondError(NikkyError):
    pass

    
def nikkysim(stripNumber=True, saying=None):
    if saying is None:
        x, y = randint(0, 4294967295), randint(0, 9999)
    else:
        x, y = saying
    out = subprocess.check_output(['nikky', '{}-{}'.format(x, y)]).decode()
    if stripNumber:
        return (out.split(': ')[1].rstrip(), (x, y))
    else:
        return (out.rstrip(), (x, y))
        
        
def nikkysimSayingNo(reMatch):
    w, x, dummy, y = reMatch.groups()
    if y is None:
        y = 0
    x, y = int(x), int(y)
    if w == 'A-' or w == 'a-':
        return "Only tev's TI-89 NikkySim can do the 'A-' quotes"
    elif w == 'B-' or w == 'b-' or w is None:
        if (x >= 0 and x <= 4294967295) and (y >= 0 and y <= 9999):
            return nikkysim(True, (x, y))[0]
        else:
            return 'Sayings go from 0-0 to 4294967295-9999, champ'
    else:
        return "No such thing as a {}type quote yet".format(w)
    
    
def qotd():
    return subprocess.check_output(['./qotd.sh', './qotd.sh']).decode()


def markovReply(msg):
    words = msg.split()
    m = {5: markov5, 4: markov4, 3: markov3, 2: markov2}
    for order in (5, 4, 3, 2):
        availReplies = []
        for i in range(len(words)):
            response = m[order].sentence_from_chain(tuple(words[i:i+order]))
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
    
    
def do_markov2(msg):
    chain = tuple(msg.split())
    if len(chain) == 1:
        response = markov2.sentence_from_word(chain[0])
    else:
        response = markov2.sentence_from_chain(chain)
    if response:
        return response
    return '"{}": chain not found'.format(' '.join(chain))


def do_markov3(msg):
    chain = tuple(msg.split())
    if len(chain) == 1:
        response = markov3.sentence_from_word(chain[0])
    else:
        response = markov3.sentence_from_chain(chain)
    if response:
        return response
    return '"{}": chain not found'.format(' '.join(chain))


def do_markov4(msg):
    chain = tuple(msg.split())
    if len(chain) == 1:
        response = markov4.sentence_from_word(chain[0])
    else:
        response = markov4.sentence_from_chain(chain)
    if response:
        return response
    return '"{}": chain not found'.format(' '.join(chain))


def do_markov5(msg):
    chain = tuple(msg.split())
    if len(chain) == 1:
        response = markov5.sentence_from_word(chain[0])
    else:
        response = markov5.sentence_from_chain(chain)
    if response:
        return response
    return '"{}": chain not found'.format(' '.join(chain))
    
    
class NikkyAI:
    def __init__(self):
        self.lastNikkysimSaying = None
        self.lastReply = None
        self.lastReplies = {}
        self.nick = 'nikkybot'
    
    def nikkysimRemark(self, msg='', stripNumber=True):
        out, self.lastNikkysimSaying = nikkysim(stripNumber)
        self.lastReply = out
        return [out]
        
    def genericRemark(self, msg=''):
        nick=''
        m = re.match(r'<(.*)>', msg)
        if m:
            nick = m.group(1)
        self.lastReply = choice(GENERIC_REMARKS).format(nick)
        return self.lastReply.split('\n')
    
    def remark(self, msg=''):
        return choice((self.nikkysimRemark(), self.genericRemark(msg)))
    
    def patternReply(self, msg, _recurseLevel=0):
        if _recurseLevel > 25:
            raise DontKnowHowToRespondError
        
        m = re.match(r'<(.*?)> (.*)', msg)
        if m:
            sourcenick = m.group(1)
            msg = m.group(2)
        else:
            sourcenick = ''
        m = re.match(re.escape(self.nick) + r'\W*(.*)', msg)
        if m:
            msg = m.group(1)
        
        topPriority = None
        matches = []
        assert self.lastReply is None or isinstance(self.lastReply, str)
        for p in PATTERN_REPLIES:
            if len(p) == 3:
                pattern, priority, action = p
                lastReply = None
            elif len(p) == 4:
                pattern, lastReply, priority, action = p
            else:
                raise IndexError('Pattern reply tuple must be length 3 or 4, not {} (pattern: {})'.format(len(p), p))
            try:
                m = re.search(pattern, msg, flags=re.I)
            except Exception as e:
                print('Regex: {}'.format(pattern))
                raise e
            if m:
                assert lastReply is None or isinstance(lastReply, str)
                if lastReply is None or re.search(lastReply, self.lastReply):
                    if topPriority is None or priority < topPriority:
                        matches = [(m, action)]
                        topPriority = priority
                    elif priority == topPriority:
                        matches.append((m, action))
        try:
            thismatch, reply = choice(matches)
        except IndexError:
            raise DontKnowHowToRespondError
        # Debug
        print()
        print(msg)
        print(thismatch.re.pattern)
        print()
        #
        try:
            reply.match = thismatch
        except AttributeError:
            pass
        if type(reply) == Recurse:
            return self.patternReply(reply, _recurseLevel=_recurseLevel+1)
        else:
            fmt = (sourcenick,) + thismatch.groups()
            try:
                self.lastReply = reply.get(fmt).format(*fmt)
            except AttributeError as e:
                raise e
                if str(e).endswith("'get'"):
                    self.lastReply = reply.format(*fmt)
                else:
                    raise e
            finally:
                try:
                    if (datetime.now() -
                            self.lastReplies[self.lastReply.lower()] <
                            PATTERN_RESPONSE_RECYCLE_TIME and not
                            isinstance(reply, E)):
                        return self.patternReply(msg, _recurseLevel + 1)
                except KeyError:
                    pass
                finally:
                    self.lastReplies[self.lastReply.lower()] = datetime.now()
                return self.lastReply.split('\n')

    def markovReply(self, msg):
        m = re.match(r'<(.*?)> (.*)', msg)
        if m:
            sourcenick = m.group(1)
            msg = m.group(2)
        else:
            sourcenick = ''
            
        if randint(0, 10):
            msg = msg.replace('nikkybot', sourcenick, 1)
        out = markovReply(msg).rstrip()
        for transform in (('nikkybot has ', 'I have '),
                          ('nikkybot is', 'I am'),
                          ('nikkybot: ', sourcenick + ': '),
                         ):
            old, new = transform
            if out.lower().startswith(old):
                out = new + out[len(old):]
                break
        out = out.replace('nikkybot', sourcenick)
        if randint(0, 10):
            out = re.sub(r'\S+: ', sourcenick + ': ', out)
        self.lastReply = out
        return self.lastReply.split('\n')
    
    def reply(self, msg):
        try:
            return self.patternReply(msg)
        except DontKnowHowToRespondError:
            return self.markovReply(msg)
            
    def decideRemark(self, msg):
        pacific = timezone('US/Pacific')    # Where Nikky lives
        hour = datetime.now(pacific).hour
        i = int(hour >= 2 and hour <= 12)   # 0 = awake; more activity
                                            # 1 = usually asleep; less activity
        try:
            potentialResponse = self.patternReply(msg)
        except DontKnowHowToRespondError:
            c = REMARK_CHANCE[2 + i]
            if re.search(r'\bnikky\b', msg, re.I):
                c = int(c/2)
            r = randint(0, c)
            #print('Remark chance {}/{}'.format(r, c))
            if not r:
                return self.remark(msg)
            else:
                return None
        else:
            c = REMARK_CHANCE[0 + i]
            if re.search(r'\bnikky\b', msg, re.I):
                c=int(c/2)
            r = randint(0, c)
            #print('Response chance {}/{}'.format(r, c))
            if not r:
                return potentialResponse
            else:
                self.lastReplies.pop('\n'.join(potentialResponse).lower())
                return None
