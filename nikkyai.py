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

from collections import deque
from datetime import datetime, timedelta
from random import randint, choice
import cPickle
from os import fstat, stat, getpid
import re
import subprocess
import psycopg2
from time import time
from twisted.python.rebuild import rebuild

import markov
rebuild(markov)        # Update in case of dynamic reload

DEFAULT_MARKOV_LENGTH=4         # Valid values:  1-4

#------------------------------------------------------------------------------


class Nikky_error(Exception):
    pass


class Dont_know_how_to_respond_error(Nikky_error):
    pass


class Bad_response_error(Nikky_error):
    pass


class Bad_personality_error(Nikky_error):
    pass


# Set up reply pattern table
import patterns
rebuild(patterns)        # Update in case of dynamic reload
import personalitiesrc


class NikkyAI(object):
    def __init__(self, db_connect='dbname=markovmix user=markovmix',
                 recurse_limit=100, debug=True, max_lf_l=1, max_lf_r=2,
                 remark_chance_no_keywords=1000, remark_chance_keywords=200,
                 pattern_response_expiry=timedelta(90),
                 personality='nikky', id=None, search_time=1,
                 context_lines=10):

        # Markov chain initialization
        self.dbconn = psycopg2.connect(db_connect)
        self.set_personality(personality)

        # Remember other options
        self.recurse_limit = recurse_limit
        self.debug = debug
        self.max_lf_l, self.max_lf_r = max_lf_l, max_lf_r
        self.remark_chance_no_keywords = remark_chance_no_keywords
        self.remark_chance_keywords = remark_chance_keywords
        self.pattern_response_expiry = pattern_response_expiry
        self.search_time = search_time

        # Init AI
        self.last_reply = ''
        self.last_replies = {}
        self.nick = 'nikkybot'
        self.last_lines = deque([], maxlen=context_lines)

        # Init state lists
        self.preferred_keywords = set()
        self.munge_list = set()
        self.replace_nicks_list = set()

        # Set up state save if ID given
        self.id = id
        self.load_state()

    def reply(self, msg, context='', add_response=True):
        """Generic reply method.  Try to use pattern_reply; if no response
        found, fall back to markov_reply.  Do check_output_response().
        """
        try:
            out = self.pattern_reply(msg, context=context,
                                     add_response=add_response)
        except Dont_know_how_to_respond_error:
            out = self.markov_reply(msg, context=context,
                                    add_response=add_response)

        # This function should be guaranteed to give a non-null output
        assert([line for line in out.split('\n') if line])
        return out

    def decide_remark(self, msg, context=''):
        """Determine whether a random response to a line not directed to
        nikkybot should be made.  Do check_output_response().
        """
        nick, msg_only = self.filter_input(msg)
        has_keywords = False
        for p in self.preferred_keywords:
            if re.search(p, msg_only, re.I):
                has_keywords = True
        c = (self.remark_chance_keywords if has_keywords
             else self.remark_chance_no_keywords)
        if not randint(0, c):
            # Output random message
            if has_keywords:
                return self.reply(msg, context=context)
            else:
                if randint(0, 1):
                    return self.remark(msg)
                else:
                    return self.reply(msg, context=context)
        return ''

    def remark(self, msg='', add_response=True):
        """Choose between a context-less predefined generic remark or a
        NikkySim remark, avoiding repeats in short succession.  Add new
        response to self.last_replies if add_response.  Do
        check_output_response().
        """
        for i in xrange(self.recurse_limit):
            try:
                return self.check_output_response(
                    self.generic_remark(msg), add_response=add_response)
            except Bad_response_error:
                pass
        return ''

    def generic_remark(self, msg=''):
        """Select a random remark from the predefined random remark list.
        check_output_response() NOT called.
        """
        nick, msg = self.filter_input(msg)
        if self.get_personality() == 'nikky':
            while True:
                p = choice(patterns.nikky_generic_remarks)
                if nick or '{0}' not in p:
                    # Don't use a pattern requiring a source nick if we don't
                    # have one
                    break
            out = p.format(nick)
            return self.dehighlight_sentence(out)
        else:
            # Not supported for non-nikky personas
            return ''

    def pattern_reply(self, msg, context='', add_response=True):
        """Generate a reply using predefined pattern/response patterns.
        Check for and avoid repeated responses.  Add new response to
        add_response to self.last_replies if add_response.
        Do check_output_response().
        """
        search_time_save = self.search_time
        for i in xrange(self.recurse_limit):
            response, allow_repeat = self._pattern_reply(msg, context)
            response = self.dehighlight_sentence(response)
            try:
                out = self.check_output_response(
                    response, allow_repeat, add_response=add_response)
            except Bad_response_error:
                self.search_time /= 2
            else:
                self.search_time = search_time_save
                return out
        raise Dont_know_how_to_respond_error

    def _pattern_reply(self, msg, context):
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
                m = re.search(pattern.format(re.escape(self.nick)), msg,
                              flags=re.I)
            except Exception as e:
                self.printdebug('[_pattern_reply] Regex: {}, {}'.format(pattern, e))
                raise e
            if m:
                # Input matches, what about last_reply?
                if last_reply is None or re.search(last_reply, self.last_reply):
                    # last_reply good, does potential response have priority?
                    # (Lower values = higher precedence)
                    if cur_priority is None or priority < cur_priority:
                        # Found higher priority, discard everything found and
                        # start again with this one
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
            self.printdebug("[_pattern_reply] sourcenick {}, msg {}: No pattern match found".format(repr(sourcenick), repr(msg)))
            raise Dont_know_how_to_respond_error
        else:
            self.printdebug("[_pattern_reply] sourcenick {}, msg {}: Chose match {}".format(repr(sourcenick), repr(msg), repr(match.re.pattern)))
        fmt_list = [sourcenick,] + [self.sanitize(s) for s in match.groups()]
        try:
            return (reply.get(self, context, fmt_list), allow_repeat)
        except AttributeError as e:
            if str(e).endswith("'get'"):
                # In case of a plain string
                return (reply.format(*fmt_list), allow_repeat)
            else:
                raise e

    def markov_reply(self, msg, context='', failmsg=None, add_response=True,
                     max_lf_l=None, max_lf_r=None, order=None):
        """Generate a reply using Markov chaining. Check and avoid repeated
        responses.  If unable to generate a suitable response, return a random
        Markov sentence if failmsg is None; else return failmsg.  Add new
        response to self.last_replies if add_response.  Do
        check_output_response().
        """
        order = order if order else self.default_markov_length
        max_lf_l, max_lf_r = self.get_max_lf(max_lf_l, max_lf_r)
        nick, msg = self.filter_input(msg)
        msg = self.filter_markov_input(nick, msg)
        if not context:
            self.printdebug('[markov_reply] No context given, using input')
            context = '{} {}'.format(nick, msg)

        words = self.markov.str_to_chain(msg)
        best_score, best_resp = 0, ''
        start_time = time()

        class ResponseTimeUp(Exception):
            pass

        try:
            while msg.strip():
                for o in (5, 4, 3, 2, 1):
                    for i in xrange(len(words) - (o-1)):
                        if time() > start_time + self.search_time:
                            raise ResponseTimeUp

                        chain = tuple(words[i:i+o])
                        try:
                            candidate = self.markov.sentence(
                                chain, forward_length=order,
                                backward_length=order,
                                max_lf_forward=max_lf_r,
                                max_lf_backward=max_lf_l)
                        except KeyError:
                            continue
                        else:
                            # Do output filtering, duplicate checks, etc.
                            candidate = self.filter_markov_output(nick,
                                                                  candidate)
                            try:
                                candidate = self.check_output_response(
                                    candidate, add_response=False)
                            except Bad_response_error:
                                continue
                            if (self.markov.conv_key(candidate) ==
                                    self.markov.conv_key(msg)):
                                continue

                            # Everything's okay, score and consider the
                            # candidate response
                            score = self.markov.get_context_score(candidate,
                                                                  context)
                            self.printdebug(
                                '[markov_reply] Score: {}, Candidate: {}'.format(
                                    score, repr(candidate)))
                            if score >= best_score:
                                best_score, best_resp = score, candidate
        except ResponseTimeUp:
            pass

        if best_resp:
            return self.check_output_response(best_resp,
                                              add_response=add_response)
        elif failmsg is None:
            return self.random_markov(src_nick=nick, add_response=add_response,
                                      order=order)
        else:
            return failmsg

    def random_markov(self, src_nick='', add_response=True,
                      max_lf_l=None, max_lf_r=None, order=None):
        """Pick any random Markov-chained sentence and output it.  Do
        check_output_response().
        """
        order = order if order else self.default_markov_length
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
                msg = self.markov.sentence(
                    chain, forward_length=order,
                    backward_length=order, max_lf_forward=max_lf_r,
                    max_lf_backward=max_lf_l)
            except KeyError:
                continue
            else:
                out = self.filter_markov_output(src_nick, msg)
                try:
                    return self.check_output_response(
                        out, add_response=add_response)
                except Bad_response_error:
                    continue
        return "I don't know what to say!"

    def markov_forward(self, chain, failmsg='', src_nick='',
                       max_lf=None, force_completion=True,
                       context='', order=None):
        """Generate sentence from the current chain forward only and not
        backward.  Do NOT do check_output_response().  Produce the best
        matching response if 'context' string is given.  Spend no more than
        'search_time' seconds looking for a response.
        """
        order = order if order else self.default_markov_length
        if max_lf is None:
            max_lf = self.max_lf_r
        if len(chain) > 5:
            chain = chain[:5]
            self.printdebug('[markov_forward] Warning: chain length too long; truncating')
        if not context:
            self.printdebug('[markov_forward] No context given')
        best_score, best_resp = 0, failmsg
        start_time = time()
        while True:
            try:
                candidate = self.markov.sentence_forward(
                    chain, length=order,
                    allow_empty_completion=not force_completion, max_lf=max_lf)
            except KeyError:
                break
            else:
                if context:
                    score = self.markov.get_context_score(candidate, context)
                    self.printdebug(
                        '[markov_forward] Score: {}, Candidate: {}'.format(
                            score, repr(candidate)))
                    if (score >= best_score):
                        best_score, best_resp = score, candidate
                else:
                    best_resp = candidate
            if ((not context and best_resp) or
                    (time() > start_time + self.search_time)):
                break
        return self.filter_markov_output(src_nick, best_resp)

    def manual_markov(self, order, msg, max_lf=None):
        """Return manually-invoked Markov operation (output special error
        string if chain not found).  Does NOT do check_output_response().
        """
        nick, msg = self.filter_input(msg)
        msg = self.filter_markov_input(nick, msg)
        chain = self.markov.str_to_chain(msg, wildcard='*')
        try:
            out = self.markov.sentence(
                chain, forward_length=order-1, backward_length=order-1,
                max_lf_forward=max_lf, max_lf_backward=max_lf)
        except KeyError:
            return '{}: Markov chain not found'.format(repr(chain))
        else:
            return out

    def manual_markov_forward(self, order, msg, max_lf=None):
        """Return manually-invoked Markov forward operation (output special
        error string if chain not found).  Do NOT do check_output_response().
        """
        nick, msg = self.filter_input(msg)
        msg = self.filter_markov_input(nick, msg)
        chain = self.markov.str_to_chain(msg, wildcard='*')
        try:
            response = self.markov.sentence_forward(chain, length=order-1,
                                                    max_lf=max_lf)
        except KeyError:
            return '{}: Markov chain not found'.format(repr(chain))
        else:
            return response

    def nikkysim(self, strip_number=False, saying=None):
        """Return NikkySim saying.  saying is the saying number as a tuple
        (e.g. (1234,5678)); None selects random saying.  Don't start output
        with saying number if strip_number is True.  Output
        (msg, saying_tuple).  Do NOT do check_output_response().
        """
        if saying is None:
            x, y = randint(0, 4294967295), randint(0, 9999)
        else:
            x, y = saying
        out = subprocess.check_output(['nikky', '{}-{}'.format(x, y)])
        out = self.dehighlight_sentence(out)
        if strip_number:
            return (out.split(': ')[1].rstrip(), (x, y))
        else:
            return (out.rstrip(), (x, y))

    def _add_state_list(self, item, container, debug_msg):
        if item not in container:
            container.add(item)
            self.printdebug(debug_msg.format(repr(item)))
            self.save_state()

    def _del_state_list(self, item, container, debug_msg):
        if item in container:
            container.remove(item)
            self.printdebug(debug_msg.format(repr(item)))
            self.save_state()
        else:
            raise KeyError(item)

    def add_preferred_keyword(self, keyword):
        """Add a preferred keyword regex pattern"""
        self._add_state_list(keyword, self.preferred_keywords,
                             'add_preferred_keyword: Added {}')

    def delete_preferred_keyword(self, keyword):
        """Remove a preferred keyword regex pattern"""
        self._del_state_list(keyword, self.preferred_keywords,
                             'delete_preferred_keyword: Removed {}')

    def add_munged_word(self, word):
        """Add a munged word regex pattern"""
        self._add_state_list(word, self.munge_list,
                             'add_munged_word: Added {}')

    def delete_munged_word(self, word):
        """Remove a munged word regex pattern"""
        self._del_state_list(word, self.munge_list,
                             'delete_munged_word: Removed {}')

    def add_replace_nick(self, nick):
        """Add a replaceable nick regex pattern"""
        self._add_state_list(nick, self.replace_nicks_list,
                             'add_replace_nick: Added {}')

    def delete_replace_nick(self, nick):
        """Remove a replaceable nick regex pattern"""
        self._del_state_list(nick, self.replace_nicks_list,
                             'delete_replace_nick: Removed {}')

    def add_last_reply(self, reply, datetime_=None):
        """Add a reply string to the last replies memory (used by
        check_output_response). datetime_ defaults to datetime.now().
        """
        if datetime_ is None:
            datetime_ = datetime.now()
        self.last_replies[self.markov.conv_key(reply)] = datetime.now()
        self.save_state()

    def check_output_response(self, response, allow_repeat=False,
                              add_response=True):
        """Throw Bad_response_error on null responses, and, if not
        allow_repeat, if the response was already output not too long ago.
        Otherwise, set response as last-used response if add_response is True,
        and return response list, split by newlines.
        """
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
        dictionary
        """
        num_removed = 0
        orig_size = len(self.last_replies)
        for k, d in self.last_replies.items():
            if (datetime.now() - d > self.pattern_response_expiry):
                self.printdebug(
                    "[clean_up_last_replies] "
                    "Removed stale last_replies entry {} ({})".format(
                        repr(k), d)
                )
                del self.last_replies[k]
                num_removed += 1
        self.printdebug(
            "[clean_up_last_replies] "
            "Removed {} items (len {} -> {})".format(
                num_removed, orig_size, len(self.last_replies))
        )
        self.save_state()

    def clear_last_replies(self):
        """Delete all last reply memory"""
        self.last_replies.clear()
        self.save_state()

    def filter_input(self, msg):
        """Preprocess input msg in form "<speaking nick> msg".
        Return (speaker_nick, msg).
        """
        m = re.match(r'<(.*?)> (.*)', msg, re.DOTALL)
        if m:
            speaker_nick, msg = m.groups()
        else:
            speaker_nick, msg = '', msg

        # Remove multiple consecutive spaces that could throw off message
        # parsing
        msg = re.sub(' +', ' ', msg)

        # Remove highlight at beginning of line, if it exists
        m = re.match(re.escape(self.nick) + r'[ :,;.!?*] *(.*)', msg, re.I)
        if m:
            msg = m.group(1)
        return (speaker_nick, msg)

    def filter_markov_input(self, sourcenick, msg):
        """Perform transformations on input before it goes to Markov
        functions:
        Replace non-UTF characters.
        Replace occurences of own nick with 'sourcenick' (if 'sourcenick' is
        non-null).
        """
        #!FIXME! Temporary workaround (?) for Twisted's Unicode crap.
        #  To do:  Something slightly less insane?
        new_msg = msg.decode(encoding='utf8', errors='replace').encode(
            encoding='utf8', errors='replace')
        if sourcenick:
            new_msg = re.sub(r'\b' + re.escape(self.nick) + r'\b', sourcenick,
                             new_msg)
        return new_msg

    def filter_markov_output(self, sourcenick, msg):
        """Perform transformations on output for Markov functions."""

        # Transform phrases at beginning of reply
        for transform in (
                    # Avoid self-references in third person
                    (self.nick + ' has ', 'I have '),
                    (self.nick + ' is', 'I am'),
                    (self.nick + ':',
                        sourcenick + ':' if sourcenick else self.nick + ':'),
                    ('nikkybot:',
                        sourcenick + ':' if sourcenick else self.nick + ':'),
                    ('nikkybot', 'nikky'),
                    ('nikkybutt', 'nikky'),
                ):
            old, new = transform
            if msg.lower().startswith(old):
                msg = new + msg[len(old):]
                break
        if sourcenick:
            msg = msg.replace(self.nick, sourcenick)

        # Transform initial highlights to a highlight to the speaker for a
        # sense of realism
        if sourcenick and randint(0, 10):
            msg = re.sub(r'^\S+: ', sourcenick + ': ', msg, count=1)

        msg = self.replace_nicks(msg, sourcenick)
        msg = self.dehighlight_sentence(msg)
        return msg

    def sanitize(self, s):
        """Remove control characters from 's' if it's a string; return it as is
        if it's None
        """
        if s is not None:
            for cn in xrange(0, 32):
                s = s.replace(chr(cn), '')
        return s

    def get_max_lf(self, max_lf_l=None, max_lf_r=None):
        """Obtain maximum number of output lines settings.  Return
        max_lf_l/max_lf_r parameter unless None, else return default setting.
        """
        if max_lf_l is None:
            max_lf_l = self.max_lf_l
        if max_lf_r is None:
            max_lf_r = self.max_lf_r
        return max_lf_l, max_lf_r

    def _set_personality_config(self, personality):
        cfg = personalitiesrc.personality_config.get(personality, {})

        self.default_markov_length = cfg.get('order', DEFAULT_MARKOV_LENGTH)

    def set_personality(self, personality):
        """Change Markov personality to given table name in Markov database"""
        personality = self.normalize_personality(personality)
        if self.is_personality_valid(personality):
            self.markov = markov.PostgresMarkov(self.dbconn, personality,
                                                case_sensitive=False)
            self.personality = personality
            self._set_personality_config(personality)
        else:
            raise Bad_personality_error

    def get_personality(self):
        """Return current Markov personality"""
        return self.personality

    def get_personalities(self):
        """Return list of available personalities"""
        reload(personalitiesrc)
        return personalitiesrc.personality_regexes.keys()

    def normalize_personality(self, personality):
        """Reduce personality to case/punctuation-insensitive form;
        resolve aliases to primary personality name"""
        personality = personality.replace('·', '')
        try:
            personality = self.markov.conv_key(personality)
        except AttributeError:
            # If self.markov hasn't been created yet (e.g., during class init),
            # fall back to lower()
            personality = personality.lower()
        # Resolve any aliases
        try:
            link = personalitiesrc.personalities[personality]
        except KeyError:
            link = None
        return self.normalize_personality(link) if link else personality

    def is_personality_valid(self, personality):
        """Return whether personality is valid and available"""
        personalities = self.get_personalities()
        return self.normalize_personality(personality) in personalities

    def get_state(self):
        """Return an object representing current persistent state data for the
        class (for storage/later restoring)
        """
        return {'last_replies': self.last_replies,
                'preferred_keywords': self.preferred_keywords,
                'munge_list': self.munge_list,
                'replace_nicks_list': self.replace_nicks_list}

    def set_state(self, state):
        """Reset current internal state to that captured by state (returned by
        get_state)
        """
        self.last_replies = state['last_replies']
        self.preferred_keywords = state['preferred_keywords']
        try:
            self.munge_list = state['munge_list']
        except KeyError:
            pass
        try:
            self.replace_nicks_list = state['replace_nicks_list']
        except KeyError:
            pass

    def load_state(self):
        """Load current internal state from DB entry"""
        if self.id is None:
            return
        cur = self.dbconn.cursor()
        self._check_state_table()
        cur.execute('SELECT state FROM ".nikkyai-state" WHERE id=%s',
                    (self.id,))
        t = cur.fetchone()
        if t is None:
            self.printdebug('[load_state] No state found for id "{}"'.format(self.id))
        else:
            self.set_state(cPickle.loads(str(t[0])))
            self.printdebug(
                '[load_state] Loaded state for id "{}"'.format(self.id))
        self.dbconn.rollback()

    def save_state(self):
        """Save current internal state to DB"""
        if self.id is None:
            return
        cur = self.dbconn.cursor()
        self._check_state_table()
        state = cPickle.dumps(self.get_state())
        try:
            cur.execute(
                'INSERT INTO ".nikkyai-state" (id, state) VALUES (%s, %s)',
                (self.id, psycopg2.Binary(state)))
        except psycopg2.IntegrityError:
            self.dbconn.rollback()
            cur.execute(
                'UPDATE ".nikkyai-state" SET state=%s WHERE id=%s',
                (psycopg2.Binary(state), self.id))
        else:
            self.printdebug('[save_state] Saved new state for id "{}"'.format(self.id))
        self.dbconn.commit()

    def _check_state_table(self):
        """Check existence of state-save table in DB; create if necessary"""
        cur = self.dbconn.cursor()
        try:
            cur.execute('CREATE TABLE ".nikkyai-state" '
                     '(id VARCHAR PRIMARY KEY, state BYTEA NOT NULL)')
        except psycopg2.ProgrammingError:
            self.dbconn.rollback()
        else:
            self.printdebug(
                '[_check_state_table] State save table does not exist; creating it')
            self.dbconn.commit()

    def munge_word(self, word):
        """Insert a symbol character into the given word (e.g., for saying
        nicks without highlighting people)
        """
        pos = randint(1, min(3, len(word)-1))
            # Make sure character is inserted within first 4 chars to properly
            # support Sax's highlighting, which only matches first 4 chars
        word = word[0:pos] + '·' + word[pos:]
        return word

    def dehighlight_sentence(self, sentence):
        """Munge any occurrences of words from munged word list that appear in
        sentence
        """
        for word in self.munge_list:
            munged = self.munge_word(word)
            sentence = re.sub(r'\b' + word + r'\b', munged,
                              sentence, flags=re.I)
        return sentence

    def replace_nicks(self, sentence, src_nick):
        """Replace words/nicks that appear in replaceable nicks list with
        src_nick if src_nick is not None or '', or if the words/nicks appear
        at the beginning of 'sentence' and appear to be a highlight."""
        if not src_nick:
            self.printdebug('[replace_nicks] Warning:  Empty src_nick')
        for nick in self.replace_nicks_list:
            if src_nick:
                sentence = re.sub(r'\b' + nick + r'\b', src_nick,
                                  sentence, flags=re.I)
            else:
                sentence = re.sub(r'^' + nick + r'(:|--|,)\s*', src_nick,
                                  sentence, flags=re.I)
        return sentence

    def printdebug(self, msg):
        """Output a debug message to stdout if debug mode is on"""
        if self.debug:
            print(msg)
