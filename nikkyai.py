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


#!TODO!
#
# State data randomly gets lost/truncated, probably related to lazy loading of
# NikkyAI objects?
#
# See about splitting up longer reply functions?
#
# Consider moving check_output_response checks to upper-level func only
#
# Move most globals to parameterized options
#
# Add mimc/impersonation feature to "what do you think of" and random remarks
# when it's ready
#
# Fix up mismatching "'()[]{}
#
# Replace nicks with current ones, and/or avoid highlighting random people
#
# Don't output responses that match input (wasn't this already done?)
#
# Markov-key-convert last replies (wasn't *this* already done before?)
#
# Don't output keywords exactly as-is (with regard to punctuation)
#
# Add response for nikkybot to tell its age
#
# When chopping line breaks, avoid cutting off actual keyword seed
#
# Merge nikkybot/markovmix
#
# More general synonym filtering/transforming (don't replace the entire input
# pattern)

from datetime import datetime, timedelta
from random import randint, choice
import cPickle
from os import fstat, stat, getpid
import re
import subprocess
import psycopg2

import markov

DEBUG = True
DB_CONNECT = 'dbname=markovmix user=markovmix'

PREFERRED_KEYWORDS_FILE = '/home/nikkybot/nikkybot/state/preferred_keywords.txt'
RECURSE_LIMIT = 100
MAX_LF_L = 1
MAX_LF_R = 2

REMARK_CHANCE_RANDOM = 700
REMARK_CHANCE_HAS_KEYWORDS = 100
PATTERN_RESPONSE_RECYCLE_TIME = timedelta(30)

#------------------------------------------------------------------------------

# !TODO! Do some proper log handling instead of print()--send debug/log stuff
# to a different stream or something.  It interferes with things like botchat


# Markov chain initialization
dbconn = psycopg2.connect(DB_CONNECT)
markov = markov.PostgresMarkov(dbconn, 'nikky', case_sensitive = False)
preferred_keywords = []

# Set up reply pattern table
import patterns
reload(patterns)        # Update in case of dynamic reload


class Nikky_error(Exception):
    pass


class Dont_know_how_to_respond_error(Nikky_error):
    pass


class Bad_response_error(Nikky_error):
    pass


class NikkyAI(object):
    def __init__(self):
        self.last_nikkysim_saying = None
        self.last_reply = ''
        self.last_replies = {}
        self.nick = 'nikkybot'
        self.load_preferred_keywords()

# Call graph:
# * = Repeated output check
#   decide_remark
#       <reply> (not directly called by decide_remark, but children are)
#           *pattern_reply
#               _pattern_reply
#           *markov_reply
#               _markov_reply
#                   *random_markov
#           *random_markov
#       *remark
#           nikkysim_remark
#               nikkysim
#           generic_remark

    def reply(self, msg, add_response=True):
        """Generic reply method.  Try to use pattern_reply; if no response
        found, fall back to markov_reply"""
        try:
            out = self.pattern_reply(msg)
        except Dont_know_how_to_respond_error:
            out = self.markov_reply(msg)

        # This function should be guaranteed to give a non-null output
        out_okay = False
        for line in out.split('\n'):
            if line.strip():
                out_okay = True
                break
        assert(out_okay)
        return out

    def decide_remark(self, msg):
        """Determine whether a random response to a line not directed to
        nikkybot should be made"""
        c = REMARK_CHANCE_RANDOM
        nick, rest_msg = self.filter_input(msg)
        for p in preferred_keywords:
            if re.search(p, rest_msg, re.I):
                c = REMARK_CHANCE_HAS_KEYWORDS
        if not randint(0, c):
            # Output random message
            if not randint(0, 1):
                self.reply(msg)
            else:
                self.remark(msg)
        return ''

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
        return ''

    def generic_remark(self, msg=''):
        """Select a random remark from the predefined random remark list"""

        nick, msg = self.filter_input(msg)
        remark = choice(patterns.generic_remarks).format(nick)

    def nikkysim_remark(self, msg='', strip_number=True):
        """Generate a NikkySim remark.  If not strip_number, include the
        saying number before the remark."""
        out, self.last_nikkysim_saying = self.nikkysim(strip_number)
        return out

    def pattern_reply(self, msg, add_response=True):
        """Generate a reply using predefined pattern/response patterns.
        Check for and avoid repeated responses.  Add new response to
        add_response to self.last_replies if add_response."""
        for i in xrange(RECURSE_LIMIT):
            response, allow_repeat = self._pattern_reply(msg)
            try:
                return self.check_output_response(
                    response, allow_repeat, add_response=add_response)
            except Bad_response_error:
                pass
        # !TODO! Shouldn't fallbacks to markov_reply be the responsibility of
        # caller?
        return self.markov_reply(msg)

    def _pattern_reply(self, msg):
        sourcenick, msg = self.filter_input(msg)

        # Find matching responses for msg, honoring priorities
        cur_priority = None
        matches = []
        for p in patterns.patterns:
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
                if last_reply is None or re.search(last_reply, self.last_reply):
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
        fmt_list = [sourcenick,] + [self.sanitize(s) for s in match.groups()]
        try:
            return (reply.get(self, fmt_list), allow_repeat)
        except AttributeError as e:
            if str(e).endswith("'get'"):
                # In case of a plain string
                return reply.format(*fmt_list)
            else:
                raise e

    # !TODO! _markov_reply no longer needs failmsg support

    def markov_reply(self, msg, add_response=True, max_lf_l=MAX_LF_L,
                     max_lf_r=MAX_LF_R):
        """Generate a reply using Markov chaining. Check and avoid repeated
        responses.  Add new response to self.last_replies if add_response."""
        for i in xrange(RECURSE_LIMIT):
            nick, msg = self.filter_input(msg)
            out = self.filter_markov_output(
                nick, self._markov_reply(nick, msg, '', max_lf_l, max_lf_r))

            try:
                out = self.check_output_response(out,
                                                 add_response=add_response)
            except Bad_response_error:
                continue
            # !TODO! Move below check to check_output_response?
            if markov.conv_key(out) == markov.conv_key(msg):
                continue
            else:
                return out
        return self.random_markov()

    def _markov_reply(self, nick, msg, failmsg=None, max_lf_l=MAX_LF_L,
                      max_lf_r=MAX_LF_R):
        """Generate a Markov-chained reply for msg"""

        # !TODO! Actually need a if-msg-empty check?
        if not msg.strip():
            return self.random_markov()
        msg = self.filter_markov_input(nick, msg)

        # Search for a sequence of input words to Markov chain from: use the
        # longest possible chain matching any regexp from preferred_patterns;
        # failing that, use the longest possible chain of any words found in
        # the Markov database.
        words = markov.str_to_chain(msg)
        high_priority_replies = {1:[]}
        low_priority_replies = {1:[]}
        for order in (5, 4, 3, 2):
            high_priority_replies[order] = []
            low_priority_replies[order] = []
            for i in xrange(len(words) - (order-1)):
                chain = tuple(words[i:i+order])
                try:
                    response = markov.adjust_line_breaks(
                        markov.sentence(chain), max_lf_l, max_lf_r)
                except KeyError:
                    continue
                else:
                    for p in preferred_keywords:
                        if re.search(p, response, re.I):
                            high_priority_replies[order].append(response)
                    else:
                        low_priority_replies[order].append(response)

        # Failing that, try to chain on the longest possible single input word,
        # prioritizing on preferred keywords/patterns
        words.sort(key=len, reverse=True)
        for word in words:
            try:
                response = markov.adjust_line_breaks(
                    markov.sentence((word,)), max_lf_l, max_lf_r)
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

        # Failing *that*, return either failmsg (or random Markov if no
        # failmsg)
        if failmsg is None:
            return self.random_markov()
        else:
            return failmsg

    def random_markov(self, max_lf_l=MAX_LF_L, max_lf_r=MAX_LF_R):
        """Pick any random Markov-chained sentence and output it"""
        generic_words = (
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
            'because', 'any', 'these', 'give', 'day', 'most', 'us')
        for i in xrange(RECURSE_LIMIT):
            chain = markov.str_to_chain(choice(generic_words))
            try:
                msg = markov.sentence(chain)
            except KeyError:
                continue
            else:
                out = markov.adjust_line_breaks(
                    self.filter_markov_output('', msg), max_lf_l, max_lf_r)
                try:
                    return self.check_output_response(out)
                except Bad_response_error:
                    continue
        return "I don't know what to say!"

    def markov_forward(self, chain, failmsg='', max_lf=MAX_LF_R):
        """Generate sentence from the current chain forward only and not
        backward"""
        try:
            out = markov.sentence_forward(chain)
        except KeyError:
            return failmsg
        else:
            out = markov.adjust_right_line_breaks(out, max_lf).strip()
            return self.filter_markov_output('', out)

    def manual_markov(self, order, msg):
        """Return manually-invoked Markov operation (output special error
        string if chain not found)"""

        # !TODO! See if it's necessary to recurse like this.  Presumably, if
        # the key is not in the DB, searching for it another 300 times isn't
        # going to change that :-P
        for i in xrange(RECURSE_LIMIT):
            nick, msg = self.filter_input(msg)
            msg = self.filter_markov_input(nick, msg)
            chain = markov.str_to_chain(msg)
            try:
                out = markov.sentence(chain, forward_length=order-1,
                                      backward_length=order-1)
            except KeyError:
                continue
            else:
                return self.filter_markov_output(nick, out)
        return '{}: Markov chain not found'.format(repr(' '.join(chain)))

    def manual_markov_forward(self, order, msg):
        """Return manually-invoked Markov forward operation (output special
        error string if chain not found)"""

        # !TODO! See if it's necessary to recurse like this.  Presumably, if
        # the key is not in the DB, searching for it another 300 times isn't
        # going to change that :-P
        for i in xrange(RECURSE_LIMIT):
            nick, msg = self.filter_input(msg)
            msg = self.filter_markov_input(nick, msg)
            chain = markov.str_to_chain(msg)
            try:
                response = markov.sentence_forward(chain, length=order-1)
            except KeyError:
                continue
            else:
                return self.filter_markov_output(nick, response)
        return '{}: Markov chain not found'.format(repr(' '.join(chain)))


    def nikkysim(self, strip_number=True, saying=None):
        """Return NikkySim saying.  saying is the saying number as a tuple
        (e.g. (1234,5678)); None selects random saying.  Don't start output
        with saying number if strip_number is True.  Output
        (msg, saying_tuple)."""
        if saying is None:
            x, y = randint(0, 4294967295), randint(0, 9999)
        else:
            x, y = saying
        out = subprocess.check_output(['nikky', '{}-{}'.format(x, y)])
        if strip_number:
            return (out.split(': ')[1].rstrip(), (x, y))
        else:
            return (out.rstrip(), (x, y))

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
        self.last_replies[markov.conv_key(reply)] = datetime.now()

    def check_output_response(self, response, allow_repeat=False,
                              add_response=True):
        """Throw Bad_response_error on null responses, and, if not
        allow_repeat, if the response was already output not too long ago.
        Otherwise, set response as last-used response if add_response is True,
        and return response list, split by newlines."""

        if not [line for line in response.split('\n') if line.strip()]:
            raise Bad_response_error
        response_key = markov.conv_key(response)
        if not allow_repeat:
            try:
                if (datetime.now() - self.last_replies[response_key]
                        < PATTERN_RESPONSE_RECYCLE_TIME):
                    raise Bad_response_error
                elif add_response:
                    self.add_last_reply(response_key)
            except KeyError:
                if add_response:
                    self.add_last_reply(response_key)

        self.last_reply = response
        return response

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

    def filter_input(self, msg):
        """Preprocess input msg in form "<speaking nick> msg".
        Return (speaker_nick, msg)."""

        m = re.match(r'<(.*)> (.*)', msg)
        if m:
            speaker_nick, msg = m.groups()
        else:
            speaker_nick, msg = '', msg

        # Remove highlight at beginning of line, if it exists
        m = re.match(re.escape(self.nick) + r'\W *(.*)', msg, re.I)
        if m:
            msg = m.group(1)
        return (speaker_nick, msg)

    def filter_markov_input(self, sourcenick, msg):
        """Perform transformations on input before it goes to Markov
        functions:
        Replace occurences of own nick with that of the speaker."""
        return re.sub(r'\b' + re.escape(self.nick) + r'\b', sourcenick,
                      msg)

    def filter_markov_output(self, sourcenick, msg):
        """Perform transformations on output for Markov functions."""

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
            if msg.lower().startswith(old):
                msg = new + out[len(old):]
                break
        msg = msg.replace(self.nick, sourcenick)

        # Transform initial highlights to a highlight to the speaker for a
        # sense of realism
        if sourcenick and randint(0, 10):
            msg = re.sub(r'\S+: ', sourcenick + ': ', msg)
        return msg.strip()

    def sanitize(self, s):
        """Remove control characters from 's' if it's a string; return it as is
        if it's None"""
        if s is not None:
            for cn in xrange(0, 32):
                s = s.replace(chr(cn), '')
        return s
