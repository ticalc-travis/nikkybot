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
reload(markov)   # DEBUG

PERSONALITIES = ('netham45', 'kevin_o', 'brandonw', 'tev', 'merth', 'randomist', 'chronomex', 'sir_lewk', 'michael_v', 'e-j', 'cricket_b', 'glk', 'kerm')
# !TODO! Do some proper log handling instead of print()--send debug/log stuff
# to a different stream or something.  It interferes with things like botchat

DEBUG = True
RECURSE_LIMIT = 100
CANDIDATES = 1
MAX_LF_L = 0
MAX_LF_R = 2


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
                s += i.get(markov, fmt)
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
    def __init__(self, string, failmsglist=None):
        self.chain = string.split(' ')
        if failmsglist is None:
            failmsglist = ['']
        self.failmsglist = failmsglist

    def get(self, who, fmt=None):
        if fmt is None:
            fmt = []
        return markov_forward(who, [x.format(*fmt) for x in self.chain],
            choice(self.failmsglist))


class Recurse(str):
    """Recursively find a response"""
    def get(self, who, fmt=None):
        if fmt is None:
            fmt = []
        try:
            return pattern_reply(self.format(*fmt), who)[0]
        except Dont_know_how_to_respond_error:
            for i in xrange(RECURSE_LIMIT):
                reply = markov_reply(who + ': ' + self.format(*fmt))
                if reply.strip():
                    return reply
            return random_markov(markovs[who, 5])


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
    False
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
        Markov_forward('bye {0}', ('bye',))
    ),
    False
),
(r'\b(thanks|thank you)\b', 1,
    R(
        Markov_forward("you're welcome", ("you're welcome",)),
    )
),

# General
(r"^(who is|who's|what is|what's|how's|how is) (.*?)\W?$", -1,
    R(
        Markov_forward('{1} is',
            ("Never heard of 'em", 'Beats me', "Don't ask me")
        )
    ),
    True
),
(r'\b(why|how come)\b', 0,
    R(
        Markov_forward('because', ("Don't know",)),
        Markov_forward('because your', ("Don't know",)),
        Markov_forward('because you', ("Don't know",)),
        Markov_forward('because of', ("Don't know",)),
        Markov_forward('because of your', ("Don't know",))
    )
),
(r'\bwhat does it mean\b', 1,
    Recurse('it means')
),
(r'\b(how much|how many|what amount)\b', -1,
    R(
        Markov_forward('enough', ('enough',)),
        Markov_forward('too many', ('too many',)),
        Markov_forward('more than you', ("Don't know",))
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
#(r'^when (can|would|should|will|are|is|am|have|was|were|do|does)\b', 1,
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
)

# === END OF DATA SECTION =====================================================


class Nikky_error(Exception):
    pass

class Dont_know_how_to_respond_error(Nikky_error):
    pass

class Repeated_response_error(Nikky_error):
    pass


# Get personality list
def get_personalities():
    return list(PERSONALITIES)


# Markov chain initialization
markovs = {}
for p in PERSONALITIES:
    for o in (2, 3, 4, 5):
        markovs[p, o] = markov.Markov_Shelved('markov/{}-markov.{}'.format(p, o),
            order=o, readonly=True, case_sensitive=False)
        markovs[p, o].default_max_left_line_breaks = MAX_LF_L
        markovs[p, o].default_max_right_line_breaks = MAX_LF_R


def to_whom(msg):
        """Determine which personality the message is addressed to and return it
        (None if no obvious addressee) and the message with the speaker and any
        inital personality highlight stripped."""

        # Strip off source nick
        m = re.match(r'<.*> (.*)', msg)
        if m:
            msg = m.group(1)
            
        # Check initial highlight
        m = re.match(r'((?:\w|-)*)\W *(.*)', msg)
        if m:
            for k in markovs.keys():
                if k[0].lower() == m.group(1).lower():
                    return m.group(1).lower(), m.group(2)
            return None, msg
        else:
            # Try to find an "internal" highlight in the message; return first match
            for p in PERSONALITIES:
                try:
                    if re.match(re.escape(p), msg, re.I):
                        return p.lower(), msg
                except KeyError:
                    return None, msg
        return None, msg


def random_markov(m):
    """Pick any random Markov-chained sentence and output it"""
    while True:
        out = m.sentence_from_chain(
            tuple(m.chain_forward.random_key())
        )
        if out.strip():
            return out


def markov_reply(msg, max_lf_l=MAX_LF_L, max_lf_r=MAX_LF_R):
    """Generate a Markov-chained reply for msg"""

    # Find who's being talked to and split it out
    who, msg = to_whom(msg)
    if not who:
        return ''
    
    if not msg.strip():
        return random_markov(markovs[who, 5])
    for order in (5, 4, 3, 2):
        words = [x for x in msg.split(' ') if x]
        avail_replies = []
        for i in xrange(len(words) - (order-1)):
            markov = markovs[who, order]
            response = \
                markov.sentence_from_chain(
                    tuple(words[i:i+order]), max_lf_l, max_lf_r
                )
            if response.strip():
                avail_replies.append(response)
        if avail_replies:
            return choice(avail_replies)
    words.sort(key=len)
    words.reverse()
    for word in words:
        response = markovs[who, 5].sentence_from_word(word, max_lf_l, max_lf_r)
        if response.strip():
            return response
    return ''


def manual_markov(order, msg, _recurse_level=0):
    who, msg = to_whom(msg)
    chain = tuple(msg.split(' '))
    if len(chain) == 1:
        markov = markovs[who, randint(2, 5)]
        response = markov.sentence_from_word(chain[0])
    else:
        markov = markovs[who, len(chain)]
        response = markov.sentence_from_chain(chain)
    if response:
        return response
    else:
        if _recurse_level < RECURSE_LIMIT:
            return manual_markov(order, msg, _recurse_level=_recurse_level+1)
        else:
            return '{}: Markov chain not found'.format(repr(' '.join(chain)))


def markov_forward(who, chain, failmsg='', max_lf=MAX_LF_R):
    """Generate sentence from the current chain forward only and not
    backward"""

    if len(chain) == 1:
        markov = markovs[who, randint(2,5)]
        if not markov.word_forward.has_key(chain[0]):
            return failmsg
        out = ' '.join(markov.from_word_forward(chain[0])).replace(' \n ', '\n')
    else:
        markov = markovs[who, len(chain)]
        if not markov.chain_forward.has_key(tuple(chain)):
            return failmsg
        out = ' '.join(markov.from_chain_forward(chain)).replace(' \n ', '\n')
    if not out.strip():
        return failmsg
    return markov.adjust_right_line_breaks(out, max_lf)


def pattern_reply(msg, who, last_used_reply='', nick='markovmix', _recurse_level=0):
    if _recurse_level > RECURSE_LIMIT:
        raise Dont_know_how_to_respond_error

    # Separate out speaker's nick if known
    m = re.match(r'<(.*)> (.*)', msg)
    if m:
        sourcenick = m.group(1)
        msg = m.group(2)
    else:
        sourcenick = ''

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
    fmt_list = (sourcenick,) + match.groups()
    else:
        if DEBUG:
            print("DEBUG: pattern_reply: sourcenick {}, msg {}: Chose match {}".format(repr(sourcenick), repr(msg), repr(match.re.pattern)))
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

    def check_output_response(self, response, who, allow_repeat=False):
        """If not allow_repeat, check if the response was already output
        not too long ago; do exception if so, else record when this response
        was last used.  Also set response as last-used response if accepted.
        If accepted, return response list, split by newlines."""

        if not allow_repeat:
            try:
                if (datetime.now() -
                    self.last_replies[response.lower().strip()] <
                        PATTERN_RESPONSE_RECYCLE_TIME):
                    raise Repeated_response_error
                else:
                    self.last_replies[response.lower()] = datetime.now()
            except KeyError:
                self.last_replies[response.lower()] = datetime.now()

        self.last_reply = response
        return ['<{}> '.format(who) + line for line in response.split('\n')]

    def pattern_reply(self, msg):
        """Generate a reply using predefined pattern/response patterns.
        Check for and avoids repeated responses."""
        who, msg = to_whom(msg)
        if not who:
            return ''
        for i in xrange(RECURSE_LIMIT):
            response, allow_repeat = \
                pattern_reply(msg, who, self.last_reply, self.nick)
            try:
                return self.check_output_response(response, who, allow_repeat)
            except Repeated_response_error:
                pass
        return self.markov_reply('{}: {}'.format(who, msg))

    def markov_reply(self, msg, _recurse_level=0):
        """Generate a reply using Markov chaining. Check and avoid repeated
        responses."""

        # Split speaker nick and rest of message
        m = re.match(r'<(.*?)> (.*)', msg)
        if m:
            sourcenick = m.group(1)
            msg = m.group(2)
        else:
            sourcenick = ''

        who = to_whom(msg)[0]
        if not who:
            return ''

        if _recurse_level > RECURSE_LIMIT:
            out = random_markov(markovs[who, 5])
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

        # Pick some candidate responses; pick the longest
        out = ''
        for i in xrange(CANDIDATES):
            candidate = markov_reply(msg.rstrip())
            if len(candidate) > len(out):
                out = candidate

        if not out.strip():
            out = random_markov(markovs[who, 5])

        try:
            return self.check_output_response(out, who)
        except Repeated_response_error:
            return self.markov_reply(msg, _recurse_level + 1)

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
            r = self.reply('{}: {}'.format(p, msg))
            if r:
                outputs.append(r)
        try:
            return choice(outputs)
        except IndexError:
            return "I'm don't know what to say!"

