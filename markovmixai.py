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
import psycopg2

from pytz import timezone

import markov
import personalitiesrc
reload(personalitiesrc)

# !TODO! Do some proper log handling instead of print()--send debug/log stuff
# to a different stream or something.  It interferes with things like botchat

PERSONALITIES = personalitiesrc.personality_regexes.keys()
PERSONALITIES.sort()

# Deprecated--remove when no code is using it anymore
def get_personalities():
    return PERSONALITIES

DEBUG = True
PREFERRED_KEYWORDS_FILE = '/home/nikkybot/nikkybot/state/preferred_keywords.txt'
RECURSE_LIMIT = 333
CANDIDATES = 50
MAX_LF_L = 4
MAX_LF_R = 4


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

    def get(self, who, fmt=None):
        s = ''
        for i in self:
            try:
                s += i.get(who, fmt)
            except AttributeError:
                s += i.format(*fmt)
        return s


class R(S):
    """Random table"""
    def get(self, who, fmt=None):
        i = choice(self)
        try:
            return i.get(who, fmt)
        except AttributeError:
            return i.format(*fmt)


class E(str):
    """Evaluate string"""
    def get(self, who, fmt=None):
        if fmt is None:
            fmt = []
        return str(eval(self.format(who, *fmt))).format(*fmt)


class Markov_forward(object):
    """Return a Markov chain from word or chain forward"""
    def __init__(self, string, failmsglist=None, max_lf_r=MAX_LF_R):
        self.chain = string.split(' ')
        self.max_lf_r = max_lf_r
        if failmsglist is None:
            failmsglist = ['']
        self.failmsglist = failmsglist

    def get(self, who, fmt=None):
        if fmt is None:
            fmt = []
        failmsg = choice(self.failmsglist)
        if DEBUG:
            print("DEBUG: Markov_forward.get: {}: {}".format(
                repr(self.chain), repr(fmt)))
        try:
            failmsg = failmsg.get(who, fmt)
        except AttributeError:
            pass
        return markov_forward(who, [x.format(*fmt) for x in self.chain],
            failmsg, self.max_lf_r)


class Manual_markov(object):
    """Return a Markov-generated phrase of the given/ order"""
    def __init__(self, order, text):
        self.order = order
        self.text = text

    def get(self, who, fmt=None):
        if fmt is None:
            fmt = []
        return manual_markov(self.order, who, self.text.format(*fmt))


class Markov(object):
    """Force standard Markov processing on the given message and return
    result, even if message would otherwise match another regexp pattern"""
    def __init__(self, text, failmsglist=None):
        if failmsglist is None:
            failmsglist = ['']
        self.failmsglist = failmsglist
        self.text = text

    def get(self, who, fmt=None):
        if fmt is None:
            fmt = []
        failmsg = choice(self.failmsglist)
        try:
            failmsg = failmsg.get(who, fmt)
        except AttributeError:
            pass
        return markov_reply(self.text.format(*fmt), failmsg)


class Recurse(str):
    """Recursively find a response"""
    def get(self, who, fmt=None):
        if fmt is None:
            fmt = []
        try:
            return pattern_reply(self.format(*fmt), who)[0]
        except (Dont_know_how_to_respond_error, RuntimeError):
            for i in xrange(RECURSE_LIMIT):
                reply = markov_reply('?{} {}'.format(who, self.format(*fmt)))
                if reply.strip():
                    return reply
            return random_markov(markovs[who])

# === DATA SECTION ============================================================

PATTERN_RESPONSE_RECYCLE_TIME = timedelta(7)

PATTERN_REPLIES = (
# Legal forms:
# pattern regexp, priority, action
# pattern regexp, priority, action, allow repeat?
# pattern regexp, last reply, priority, action, allow repeat?

# Basics
(r'\b(hi|hello|hey)\b', 1,
    R(
        Markov_forward('hi {0}', ('hi',)),
        Markov_forward('hello {0}', ('hello',)),
        Markov_forward('hey {0}', ('hey',)),
        Markov_forward('sup {0}', ('sup',)),
    ),
    True
),
(r"\b(good night|goodnight|g'?night)\b", 1,
    R(
        Markov_forward('night {0}', ('night',)),
        Markov_forward('sweet dreams', ('night',))
    )
),
(r"\b(bye|bye bye|goodbye|good bye|see you later|night|good night|g'night)\b",
1,
    R(
        Markov_forward('bye {0}', ('bye',)),
        Markov_forward('bye'),
        Markov_forward('goodbye', ('goodbye',)),
        Markov_forward('see you', ('see you')),
        Markov_forward('cya'),
    ),
    True
),
(r"\b(congratulations|congrats)", 1,
    R(
        Markov_forward('Thanks'),
        Markov_forward('thx'),
        Markov_forward('ty'),
    ),
),
(r'\b(thanks|thank you)\b', 1,
    R(
        Markov_forward("you're welcome", ("you're welcome",)),
    )
),
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
        Recurse('how many'),
    ),
),
(r"^(who is|who's|what is|what's|how's|how is) (the |a |an |your |my )?(.*?)\?*$", 0,
    R(
        Markov_forward('{3} is'),
        Markov_forward('{3}'),
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
(r'\b(why|how come)\b', 0,
    R(
        Markov_forward('because'),
        Markov_forward('because your'),
        Markov_forward('because you'),
        Markov_forward('because of'),
        Markov_forward('because of your')
    )
),
(r'\bwhat does it mean\b', 1,
    Markov_forward('it means')
),
(r'\bcontest\b', 1,
    R(
        Recurse("I'm entering"),
        Recurse("You'll lose"),
        Recurse('My entry'),
        Markov_forward('Contests')
    )
),
(r'\b(who|what) (does|do|did|should|will|is) \S+ (.*?)\?*$', -1,
    Recurse('what do you think about {3}')
),
(r'\b(how much|how many|what amount)\b', -1,
    R(
        Markov_forward('enough'),
        Markov_forward('too many'),
        Markov_forward('more than you')
    )
),
(r"^where\b", 1,
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
        Markov_forward('up')
    )
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
(r'^when\b', 1,
    R(
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
(r'^how (can|would|should|will|are|is|am|have|was|were|do|does)\b', 1,
    R(
        Markov_forward('by'),
        Markov_forward('via'),
        Markov_forward('using'),
        Markov_forward('better than'),
        Markov_forward('worse than'),
    )
),
(r'\bwhat time\b', 0,
    R(
        Markov_forward('time for'),
        Markov_forward("it's time"),
    ),
),

# Meta
(r'(Do )?you like (.*)(.*?)\W?$', 0,
    R(
        Recurse('what do you think about {2}'),
    )
),
(r'\byou are (a |an |)\b(.*)\b', 1,
    R(
        Markov_forward('I am', ("I don't know what to say to that.",)),
        Markov_forward("I'm", ("I don't know what to say to that.",)),
        Markov_forward('I am really', ("I don't know what to say to that.",)),
        Markov_forward("I'm really", ("I don't know what to say to that.",)),
        Markov_forward('I am actually', ("I don't know what to say to that.",)),
        Markov_forward("I'm actually", ("I don't know what to say to that.",)),
    )
),
(r"^(what do you think|how do you feel|(what is|what's|what are) your (thought|thoughts|opinion|opinions|idea|ideas)) (about |of |on )(a |the |an )?(.*?)\W?$", -1,
    R(
        Markov_forward('{6}',
            ('Dunno', 'No idea', "Don't know", 'Never heard of that')
        )
    ),
    True
),
(r"^(what do you think|how do you feel|(what is|what's|what are) your (thought|thoughts|opinion|opinions|idea|ideas)) (about |of |on )(a |the |an )?me\W?$", -2,
    R(Markov_forward('you'))
),
(r"\btell me about (.*)", -2, R(Recurse('{1}'))),
(r"^(how is|how's|do you like|you like) (.*?)\W?$", -1,
    Recurse('what do you think of {2}')
),
(r'\bI \S+ you', 0,
    S(
        R('Great\n', 'gee\n', 'thanks\n', 'Awesome\n'),
        R(
            Markov_forward('I wish you'),
            Markov_forward('I hope you'),
            Markov_forward('I hope your'),
        ),
    ),
),
(r'\b(you are|you must) (a |an |)(.*)', 1,
    R(
        Markov_forward('I am'),
        Markov_forward("I'm"),
        Markov_forward('I am really'),
        Markov_forward("I'm really"),
        Markov_forward('I am actually'),
        Markov_forward("I'm actually"),
    )
),
(r"\b(what do you think|how do you feel|(what is|what's|what are) your (thought|thoughts|opinion|opinions|idea|ideas)) (about |of |on )(a |the |an )?(.*?)\W?$", -1,
    R(
        Markov_forward('{6} is'),
        Markov_forward('{6}'),
        Markov_forward('better than'),
        Markov_forward('worse than'),
    ),
    False
),
(r"^(what do you think|what do you know|how do you feel|(what is|what's|what are) your (thought|thoughts|opinion|opinions|idea|ideas)) (about |of |on )me\W?$", -2,
    R(
        Markov_forward('you'),
        Recurse('what do you think of {0}')
    )
),
(r"^(how is|how's|do you like|you like|you liek) (.*?)\W?$", -1,
    Recurse('what do you think of {2}')
),
(r"\btell (me|us) about (.*)", -2, R(Recurse('{2}'))),

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


# Markov chain initialization
dbconn = psycopg2.connect('dbname=markovmix user=markovmix')
markovs = {}
for p in PERSONALITIES:
    markovs[p] = markov.PostgresMarkov(dbconn, p, case_sensitive=False)
preferred_keywords = []


def to_whom(msg):
        """Determine which personality the message is addressed to and return it
        (None if no obvious addressee) and the message with the speaker and any
        inital personality highlight stripped."""

        # Strip off source nick
        m = re.match(r'<.*> (.*)', msg)
        if m:
            msg = m.group(1)

        # Check initial highlight
        m = re.match(r'^\?(\S+)[:,]*\W(.*)', msg)
        if m:
            for k in markovs.keys():
                if k.lower() == m.group(1).lower():
                    return m.group(1).lower(), m.group(2)
            return None, msg
        return None, msg


def random_markov(markov):
    """Pick any random Markov-chained sentence and output it"""
    while True:
        try:
            return markov.sentence(
                markov.str_to_chain(choice((
                    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have',
                    'I', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you',
                    'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they',
                    'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one',
                    'all', 'would', 'there', 'their', 'what', 'so', 'up',
                    'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
                    'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him',
                    'know', 'take', 'people', 'into', 'year', 'your', 'good',
                    'some', 'could', 'them', 'see', 'other', 'than', 'then',
                    'now', 'look', 'only', 'come', 'its', 'over', 'think',
                    'also', 'back', 'after', 'use', 'two', 'how', 'our',
                    'work', 'first', 'well', 'way', 'even', 'new', 'want',
                    'because', 'any', 'these', 'give', 'day', 'most', 'us'
                )))
            )
        except KeyError:
            continue
        else:
            break

def markov_reply(msg, failmsg='', max_lf_l=MAX_LF_L, max_lf_r=MAX_LF_R):
    """Generate a Markov-chained reply for msg"""

    # Search for a sequence of input words to Markov chain from: use the
    # longest possible chain matching any regexp from preferred_patterns;
    # failing that, use the longest possible chain of any words found in the
    # Markov database.
    who, msg = to_whom(msg)
    if who is None:
        return failmsg
    if not msg.strip():
        return random_markov(markovs[who])
    markov = markovs[who]

    words = markov.str_to_chain(msg)
    high_priority_replies = {1:[]}
    low_priority_replies = {1:[]}
    for order in (5, 4, 3, 2):
        high_priority_replies[order] = []
        low_priority_replies[order] = []
        for i in xrange(len(words) - (order-1)):
            chain = tuple(words[i:i+order])
            try:
                response = markov.adjust_line_breaks(markov.sentence(chain),
                                                     max_lf_l, max_lf_r)
            except KeyError:
                continue
            else:
                for p in preferred_keywords:
                    if re.search(p, response, re.I):
                        high_priority_replies[order].append(response)
                else:
                    low_priority_replies[order].append(response)

    # Failing that, try to chain on the longest possible single input word
    words.sort(key=len)
    words.reverse()
    for word in words:
        try:
            response = markov.adjust_line_breaks(markov.sentence((word,)),
                                                 max_lf_l, max_lf_r)
        except KeyError:
            continue
        else:
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
    if not failmsg:
        return random_markov(markovs[who])
    else:
        return failmsg


def manual_markov(order, who, msg, _recurse_level=0):
    markov = markovs[who]
    chain = markov.str_to_chain(msg)
    try:
        response = markov.sentence(chain, forward_length=order-1,
                                backward_length=order-1)
    except KeyError:
        if _recurse_level < RECURSE_LIMIT:
            return manual_markov(order, who, msg,
                                 _recurse_level=_recurse_level+1)
        else:
            return '{}: Markov chain not found'.format(repr(' '.join(chain)))
    else:
        response = markov.adjust_line_breaks(response, MAX_LF_L, MAX_LF_R)
        return response


def markov_forward(who, chain, failmsg='', max_lf=MAX_LF_R):
    """Generate sentence from the current chain forward only and not
    backward"""
    markov = markovs[who]
    try:
        response = markov.sentence_forward(chain)
    except KeyError:
        return failmsg
    else:
        return markov.adjust_right_line_breaks(response, max_lf)


def pattern_reply(msg, who, last_used_reply='', nick='markovmix'):

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
        return (reply.get(who, fmt_list), allow_repeat)
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
        self.nick = 'markovmix'

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

    def check_output_response(self, response, who, allow_repeat=False,
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
        return ['<{}> '.format(who) + line for line in response.split('\n')]

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

    def pattern_reply(self, msg, add_response=True):
        """Generate a reply using predefined pattern/response patterns.
        Check for and avoid repeated responses.  Add new response to
        add_response to self.last_replies if add_response."""
        who, msg = to_whom(msg)
        if not who:
            return ''
        for i in xrange(RECURSE_LIMIT):
            response, allow_repeat = \
                pattern_reply(msg, who, self.last_reply, self.nick)
            try:
                return self.check_output_response(
                    response, who, allow_repeat, add_response=add_response)
            except Bad_response_error:
                pass
        return self.markov_reply(msg)


    def markov_reply(self, msg, add_response=True,_recurse_level=0):
        """Generate a reply using Markov chaining. Check and avoid repeated
        responses.  Add new response to self.last_replies if add_response."""

        # Split speaker nick and rest of message
        m = re.match(r'<(.*?)> (.*)', msg)
        if m:
            sourcenick = m.group(1)
            msg = m.group(2)
        else:
            sourcenick = ''
        if msg.startswith('{}: '.format(self.nick.lower())):
            msg = msg[len(self.nick) + 2:]

        who = to_whom(msg)[0]
        if not who:
            return ''

        if _recurse_level > RECURSE_LIMIT:
            out = random_markov(markovs[who])
            return ['<{}> '.format(who) + line for line in out.split('\n')]

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
            out = self.check_output_response(out, who,
                                              add_response=add_response)
        except Bad_response_error:
            out = self.markov_reply(msg, _recurse_level=_recurse_level+1)
        if markovs[who].conv_key('\n'.join(out)) == \
                markovs[who].conv_key(msg):
            return self.markov_reply(msg, _recurse_level=_recurse_level+1)
        else:
            return out

    def reply(self, msg):
        """Generic reply method.  Try to use pattern_reply; if no response
        found, fall back to markov_reply"""

        try:
            return self.pattern_reply(msg)
        except Dont_know_how_to_respond_error:
            return self.markov_reply(msg)

    def anybody_reply(self, msg):
        """Query all personalities for a response; output one"""
        m = re.match(r'<(.*?)> (.*)', msg)
        if m:
            sourcenick = m.group(1)
            msg = m.group(2)
        else:
            sourcenick = ''
        outputs = []
        for p in PERSONALITIES:
            r = self.reply('?{} {}'.format(p, msg))
            if r:
                outputs.append(r)
        try:
            return choice(outputs)
        except IndexError:
            return "I don't know what to say!"

