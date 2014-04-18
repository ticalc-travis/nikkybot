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
# Add mimic/impersonation feature to "what do you think of" and random remarks
# when it's ready
#
# Fix up mismatching "'()[]{}
#
# Replace nicks with current ones, and/or avoid highlighting random people
#
# Don't output keywords exactly as-is (with regard to punctuation)
#
# Add response for nikkybot to tell its age
#
# When chopping line breaks, avoid cutting off actual keyword seed
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

#------------------------------------------------------------------------------


# Set up reply pattern table
import patterns
reload(patterns)        # Update in case of dynamic reload
import personalitiesrc
reload(personalitiesrc)        # Update in case of dynamic reload


class Nikky_error(Exception):
    pass


class Dont_know_how_to_respond_error(Nikky_error):
    pass


class Bad_response_error(Nikky_error):
    pass


class Bad_personality_error(Nikky_error):
    pass


class NikkyAI(object):
    def __init__(self, db_connect='dbname=markovmix user=markovmix',
                 preferred_keywords_file=None, recurse_limit=100,
                 debug=True, max_lf_l=1, max_lf_r=2,
                 remark_chance_no_keywords = 700, remark_chance_keywords=100,
                 pattern_response_expiry=timedelta(30),
                 personality='nikky'):

        # Markov chain initialization
        self.personalities = personalitiesrc.personality_regexes
        self.dbconn = psycopg2.connect(db_connect)
        self.set_personality(personality)
        self.preferred_keywords = []
        self.preferred_keywords_file = preferred_keywords_file

        # Remember other options
        self.recurse_limit = recurse_limit
        self.debug = debug
        self.max_lf_l, self.max_lf_r = max_lf_l, max_lf_r
        self.remark_chance_no_keywords = remark_chance_no_keywords
        self.remark_chance_keywords = remark_chance_keywords
        self.pattern_response_expiry = pattern_response_expiry

        # Init AI
        self.last_nikkysim_saying = None
        self.last_reply = ''
        self.last_replies = {}
        self.nick = 'nikkybot'
        self.load_preferred_keywords()

    def reply(self, msg, add_response=True):
        """Generic reply method.  Try to use pattern_reply; if no response
        found, fall back to markov_reply.  Do check_output_response()."""
        try:
            out = self.pattern_reply(msg, add_response=add_response)
        except Dont_know_how_to_respond_error:
            out = self.markov_reply(msg, add_response=add_response)

        # This function should be guaranteed to give a non-null output
        assert([line for line in out.split('\n') if line])
        return out

    def decide_remark(self, msg):
        """Determine whether a random response to a line not directed to
        nikkybot should be made.  Do check_output_response()."""
        c = self.remark_chance_no_keywords
        nick, msg = self.filter_input(msg)
        for p in self.preferred_keywords:
            if re.search(p, msg, re.I):
                c = self.remark_chance_keywords
        if not randint(0, c):
            print(msg)
            # Output random message
            if not randint(0, 1):
                return self.reply(msg)
            else:
                return self.remark(msg)
        return ''

    def remark(self, msg='', add_response=True):
        """Choose between a context-less predefined generic remark or a
        NikkySim remark, avoiding repeats in short succession.  Add new
        response to self.last_replies if add_response.  Do
        check_output_response()."""
        for i in xrange(self.recurse_limit):
            try:
                return self.check_output_response(
                    choice((self.nikkysim_remark(), self.generic_remark(msg))),
                    add_response=add_response
                )
            except Bad_response_error:
                pass
        return ''

    def generic_remark(self, msg=''):
        """Select a random remark from the predefined random remark list.
        check_output_response() NOT called."""
        nick, msg = self.filter_input(msg)
        if self.get_personality() == 'nikky':
            return choice(patterns.nikky_generic_remarks).format(nick)
        else:
            # Not supported for non-nikky personas
            return ''

    def nikkysim_remark(self, msg='', strip_number=True):
        """Generate a NikkySim remark.  If not strip_number, include the
        saying number before the remark.  check_output_response NOT called."""
        out, self.last_nikkysim_saying = self.nikkysim(strip_number)
        return out

    def pattern_reply(self, msg, add_response=True):
        """Generate a reply using predefined pattern/response patterns.
        Check for and avoid repeated responses.  Add new response to
        add_response to self.last_replies if add_response.
        Do check_output_response()."""
        for i in xrange(self.recurse_limit):
            response, allow_repeat = self._pattern_reply(msg)
            try:
                return self.check_output_response(
                    response, allow_repeat, add_response=add_response)
            except Bad_response_error:
                pass
        raise Dont_know_how_to_respond_error

    def _pattern_reply(self, msg):
        sourcenick, msg = self.filter_input(msg)

        # Find matching responses for msg, honoring priorities
        cur_priority = None
        matches = []
        if self.get_personality() == 'nikky':
            pats = patterns.nikky_patterns
        else:
            pats = patterns.global_patterns
        for p in pats:
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
                m = re.search(pattern.format(self.nick), msg, flags=re.I)
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
            if self.debug:
                print("DEBUG: pattern_reply: sourcenick {}, msg {}: No pattern match found".format(repr(sourcenick), repr(msg)))
            raise Dont_know_how_to_respond_error
        else:
            if self.debug:
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

    def markov_reply(self, msg, failmsg=None, add_response=True,
                     max_lf_l=None, max_lf_r=None):
        """Generate a reply using Markov chaining. Check and avoid repeated
        responses.  If unable to generate a suitable response, return a random
        Markov sentence if failmsg is None; else return failmsg.  Add new
        response to self.last_replies if add_response.  Do
        check_output_response()."""
        max_lf_l, max_lf_r = self.get_max_lf(max_lf_l, max_lf_r)

        for i in xrange(self.recurse_limit):
            nick, msg = self.filter_input(msg)
            out = self.filter_markov_output(
                nick, self._markov_reply(nick, msg, max_lf_l, max_lf_r))
            try:
                out = self.check_output_response(
                    out, add_response=add_response)
            except Bad_response_error:
                continue
            if self.markov.conv_key(out) == self.markov.conv_key(msg):
                continue
            return out
        if failmsg is None:
            return self.random_markov(add_response=add_response)
        else:
            return failmsg

    def _markov_reply(self, nick, msg, max_lf_l, max_lf_r):
        """Generate a Markov-chained reply for msg"""

        # Search for a sequence of input words to Markov chain from: use the
        # longest possible chain matching any regexp from preferred_patterns;
        # failing that, use the longest possible chain of any words found in
        # the Markov database.
        words = self.markov.str_to_chain(msg)
        high_priority_replies = {1:[]}
        low_priority_replies = {1:[]}
        for order in (5, 4, 3, 2):
            high_priority_replies[order] = []
            low_priority_replies[order] = []
            for i in xrange(len(words) - (order-1)):
                chain = tuple(words[i:i+order])
                try:
                    response = self.markov.adjust_line_breaks(
                        self.markov.sentence(chain), max_lf_l, max_lf_r)
                except KeyError:
                    continue
                else:
                    for p in self.preferred_keywords:
                        if re.search(p, response, re.I):
                            high_priority_replies[order].append(response)
                    else:
                        low_priority_replies[order].append(response)

        # Failing that, try to chain on the longest possible single input word,
        # prioritizing on preferred keywords/patterns
        words.sort(key=len, reverse=True)
        for word in words:
            try:
                response = self.markov.adjust_line_breaks(
                    self.markov.sentence((word,)), max_lf_l, max_lf_r)
            except KeyError:
                continue
            else:
                for p in self.preferred_keywords:
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

        # Failing *that*, return null and let caller deal with it
        return ''

    def random_markov(self, add_response=True, max_lf_l=None,
                      max_lf_r=None):
        """Pick any random Markov-chained sentence and output it.  Do
        check_output_response()."""
        max_lf_l, max_lf_r = self.get_max_lf(max_lf_l, max_lf_r)
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
        for i in xrange(self.recurse_limit):
            chain = self.markov.str_to_chain(choice(generic_words))
            try:
                msg = self.markov.sentence(chain)
            except KeyError:
                continue
            else:
                out = self.markov.adjust_line_breaks(
                    self.filter_markov_output('', msg), max_lf_l, max_lf_r)
                try:
                    return self.check_output_response(
                        out, add_response=add_response)
                except Bad_response_error:
                    continue
        return "I don't know what to say!"

    def markov_forward(self, chain, failmsg='', max_lf=None):
        """Generate sentence from the current chain forward only and not
        backward.  Do NOT do check_output_response()."""
        if max_lf is None:
            max_lf = self.max_lf_r
        try:
            out = self.markov.sentence_forward(chain)
        except KeyError:
            return failmsg
        else:
            out = self.markov.adjust_right_line_breaks(out, max_lf).strip()
            return self.filter_markov_output('', out)

    def manual_markov(self, order, msg):
        """Return manually-invoked Markov operation (output special error
        string if chain not found).  Does NOT do check_output_response()."""
        nick, msg = self.filter_input(msg)
        msg = self.filter_markov_input(nick, msg)
        chain = self.markov.str_to_chain(msg)
        try:
            out = self.markov.sentence(
                chain, forward_length=order-1, backward_length=order-1)
        except KeyError:
            return '{}: Markov chain not found'.format(repr(' '.join(chain)))
        else:
            return self.filter_markov_output(nick, out)

    def manual_markov_forward(self, order, msg):
        """Return manually-invoked Markov forward operation (output special
        error string if chain not found).  Do NOT do
        check_output_response()."""
        nick, msg = self.filter_input(msg)
        msg = self.filter_markov_input(nick, msg)
        chain = self.markov.str_to_chain(msg)
        try:
            response = self.markov.sentence_forward(chain, length=order-1)
        except KeyError:
            return '{}: Markov chain not found'.format(repr(' '.join(chain)))
        else:
            return self.filter_markov_output(nick, response)

    def nikkysim(self, strip_number=True, saying=None):
        """Return NikkySim saying.  saying is the saying number as a tuple
        (e.g. (1234,5678)); None selects random saying.  Don't start output
        with saying number if strip_number is True.  Output
        (msg, saying_tuple).  Do NOT do check_output_response()."""
        if saying is None:
            x, y = randint(0, 4294967295), randint(0, 9999)
        else:
            x, y = saying
        out = subprocess.check_output(['nikky', '{}-{}'.format(x, y)])
        if strip_number:
            return (out.split(': ')[1].rstrip(), (x, y))
        else:
            return (out.rstrip(), (x, y))

    def load_preferred_keywords(self):
        """Load a list of preferred keyword patterns for markov_reply"""
        if self.preferred_keywords_file is None:
            return
        fn = self.preferred_keywords_file
        with open(fn, 'r') as f:
            pk = [L.strip('\n') for L in f.readlines()]
        self.preferred_keywords = pk
        if self.debug:
            print("load_preferred_keywords: {} patterns loaded from {}".format(len(pk), repr(fn)))

    def save_preferred_keywords(self):
        """Save a list of preferred keyword patterns for markov_reply"""
        if self.preferred_keywords_file is None:
            return
        fn = self.preferred_keywords_file
        with open(fn, 'w') as f:
            f.writelines([s+'\n' for s in sorted(self.preferred_keywords)])
        if self.debug:
            print("save_preferred_keywords: {} patterns saved to {}".format(len(self.preferred_keywords), repr(fn)))

    def add_preferred_keyword(self, keyword):
        """Convenience function for adding a single keyword pattern to the
        preferred keywords pattern list"""
        if keyword not in self.preferred_keywords:
            self.preferred_keywords.append(keyword)
            print("add_preferred_keyword: Added keyword {}".format(repr(keyword)))
            self.save_preferred_keywords()

    def add_last_reply(self, reply, datetime_=None):
        """Convenience function to add a reply string to the last replies
        memory (used by check_output_response). datetime_ defaults to
        datetime.now()."""
        if datetime_ is None:
            datetime_ = datetime.now()
        self.last_replies[self.markov.conv_key(reply)] = datetime.now()

    def check_output_response(self, response, allow_repeat=False,
                              add_response=True):
        """Throw Bad_response_error on null responses, and, if not
        allow_repeat, if the response was already output not too long ago.
        Otherwise, set response as last-used response if add_response is True,
        and return response list, split by newlines."""
        if not [line for line in response.split('\n') if line.strip()]:
            raise Bad_response_error
        response_key = self.markov.conv_key(response)
        if not allow_repeat:
            try:
                if (datetime.now() - self.last_replies[response_key]
                        < self.pattern_response_expiry):
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
            if (datetime.now() - d > self.pattern_response_expiry):
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
        # !FIXME! Use self.nick, not hardcoded crap.  And maybe re.sub, too
        for transform in (
                    # Avoid self-references in third person
                    (self.nick + ' has ', 'I have '),
                    (self.nick + ' is', 'I am'),
                    (self.nick + ':',
                        sourcenick + ':' if sourcenick else ''),
                    ('nikkybot:',
                        sourcenick + ':' if sourcenick else ''),
                    ('nikkybot', 'nikky'),
                ):
            old, new = transform
            if msg.lower().startswith(old):
                msg = new + msg[len(old):]
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

    def get_max_lf(self, max_lf_l=None, max_lf_r=None):
        """Convenience function to obtain maximum number of output lines
        settings.  Return max_lf_l/max_lf_r parameter unless None, in which
        case return default setting."""
        if max_lf_l is None:
            max_lf_l = self.max_lf_l
        if max_lf_r is None:
            max_lf_r = self.max_lf_r
        return max_lf_l, max_lf_r

    def set_personality(self, personality):
        """Change Markov personality to given table name in Markov database"""
        personality = personality.lower().strip()
        if personality in self.personalities:
            self.markov = markov.PostgresMarkov(self.dbconn, personality,
                                                case_sensitive=False)
            self.personality = personality
        else:
            raise Bad_personality_error

    def get_personality(self):
        """Return current Markov personality"""
        return self.personality
