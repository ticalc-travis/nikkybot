# -*- coding: utf-8 -*-

# Simple Markov chain implementation
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

from collections import defaultdict, Counter, MutableMapping
from random import choice, randint
import re
import shelve
import cPickle
import psycopg2

DEFAULT_IGNORE_CHARS = '\\]\\-!"&`()*,./:;<=>?[\\^=\'{|}~'

class Markov(object):
    """tev's Markov chain implementation"""

    def __init__(self, order=2, case_sensitive=True,
            ignore_chars=DEFAULT_IGNORE_CHARS,
            default_max_left_line_breaks=None, default_max_right_line_breaks=None):
        self._order = order
        self._case_sensitive = case_sensitive
        self._ignore_chars = ignore_chars
        self.default_max_left_line_breaks = None
        self.default_max_right_line_breaks = None

        self.word_forward = defaultdict(Counter)
        self.chain_forward = defaultdict(Counter)
        self.word_backward = defaultdict(Counter)
        self.chain_backward = defaultdict(Counter)

    def get_order(self):
        """Retrieve order of Markov chain"""
        return self._order

    def conv_key(self, s):
        """Convert a string or sequence of strings to lowercase if case
        sensitivity is disabled, and strip characters contained in
        self._ignore_chars"""
        try:
            s.lower()
        except AttributeError:
            if self._case_sensitive:
                s = [re.sub('[{}]'.format(self._ignore_chars), '', x) for x in s]
            else:
                s = [re.sub('[{}]'.format(self._ignore_chars), '', x).lower()
                    for x in s]
            return s
        else:
            if self._case_sensitive:
                s = re.sub('[{}]'.format(self._ignore_chars), '', s)
            else:
                s = re.sub('[{}]'.format(self._ignore_chars), '', s).lower()
            return s

    def adjust_left_line_breaks(self, string, max):
        """Limit newline characters in string to 'max' total, counting from end of
        string backward; truncate any additional newlines and everything before
        them. None for 'max' means unlimited (return string unchanged)."""
        if max is not None:
            return '\n'.join(string.split('\n')[-max-1:])
        return string

    def adjust_right_line_breaks(self, string, max):
        """Limit newline characters in string to 'max' total, counting from
        start of string forward; truncate any additional newlines and
        everything after them. None for 'max' means unlimited (return string
        unchanged)."""
        if max is not None:
            return '\n'.join(string.split('\n')[0:max+1])
        return string

    def _add(self, words, word_dict, chain_dict):
        for i, word in enumerate(words):
            order = self._order
            chain = words[i:i+self._order+1]
            chain = tuple(chain)
            word_value = chain[:order]
            word_key = self.conv_key(word)
            chain_value = chain[1:order+1]
            chain_key = tuple(self.conv_key(chain[:order]))

            # The explicit retrieval and storing of the dictionary (rather
            # than operating on it in-place) is required in case the object
            # is shelved
            d = word_dict[word_key]
            if not word_value in d:
                d[word_value] = 1
            else:
                d[word_value] += 1
            word_dict[word_key] = d
            d = chain_dict[chain_key]
            if not chain_value in chain_dict[chain_key]:
                d[chain_value] = 1
            else:
                d[chain_value] += 1
            chain_dict[chain_key] = d

    def add(self, sentence):
        """Parse and add a string of words to the chain"""
        words = sentence.replace('\n', ' \n ').split(' ')
        words = [x.strip(' ') for x in words]
        self._add(words, self.word_forward, self.chain_forward)
        words.reverse()
        self._add(words, self.word_backward, self.chain_backward)

    def train(self, filename):
        """Train from all lines from the given text file"""
        f = open(filename, 'r')
        for line in f:
            self.add(line)

    def clear(self):
        """Delete all trained data; restart with a completely empty state"""
        self.word_forward.clear()
        self.word_backward.clear()
        self.chain_forward.clear()
        self.chain_backward.clear()

    def choice(self, counter):
        """Select a random element from Counter 'counter', weighted by the
        elements' counts"""
        if not counter:
            raise IndexError('Counter object is empty')
        total = sum(counter.values())
        targetidx = randint(0, total)
        currentidx = 0
        for k in counter.keys():
            currentidx += counter[k]
            if currentidx >= targetidx:
                return k

    def get_chain_forward(self, chain):
        """Select and return a chain from the given chain forward in context"""
        try:
            return self.choice(
                self.chain_forward[tuple(self.conv_key(chain))])
        except IndexError:
            return ()

    def get_chain_backward(self, chain):
        """Select and return a chain from the given chain backward in context"""
        try:
            return self.choice(
                self.chain_backward[tuple(self.conv_key(chain))])
        except IndexError:
            return ()

    def from_chain_forward(self, chain):
        """Generate a chain from the given chain forward in context"""

        # Get original case/punctuation
        orig_chain = list(self.get_chain_forward(chain))
        if not orig_chain:
            return ()
        l = self.get_chain_backward(tuple(reversed(chain)))
        r = list(orig_chain[:self._order-1])
        if len(l) == self._order and len(r) == self._order-1:
            orig_chain = [l[-2]] + r
        else:
            orig_chain = chain
        out = list(orig_chain)

        # Complete forward
        while chain:
            chain = self.get_chain_forward(chain)
            try:
                out.append(chain[self._order-1])
            except IndexError:
                pass
        return out

    def from_chain_backward(self, chain):
        """Generate a chain from the given chain backward in context"""

        # Get original case
        orig_chain = list(self.get_chain_backward(chain))
        if not orig_chain:
            return ()
        l = self.get_chain_forward(tuple(reversed(chain)))
        r = list(orig_chain[:self._order-1])
        if len(l) == self._order and len(r) == self._order-1:
            orig_chain = [l[-2]] + r
        else:
            orig_chain = list(chain)
        out = orig_chain

        # Complete backward
        while chain:
            chain = self.get_chain_backward(chain)
            try:
                out.append(chain[self._order-1])
            except IndexError:
                pass
        out.reverse()
        return out

    def from_word_forward(self, word):
        """Generate a chain from the given word forward in context"""
        try:
            chain = self.choice(self.word_forward[self.conv_key(word)])
        except IndexError:
            return ()
        return self.from_chain_forward(chain)

    def from_word_backward(self, word):
        """Generate a chain from the given word backward in context"""
        try:
            chain = self.choice(self.word_backward[self.conv_key(word)])
        except IndexError:
            return ()
        return self.from_chain_backward(chain)

    def sentence_from_word(self, word, max_left_line_breaks=-1,
            max_right_line_breaks=-1):
        """Generate a full saying from the given word.  Search for a
        chain going forward and then complete the sentence by also searching
        backward and combining the pieces."""

        if max_left_line_breaks == -1:
            max_left_line_breaks = self.default_max_left_line_breaks
        if max_right_line_breaks == -1:
            max_right_line_breaks = self.default_max_right_line_breaks

        fwb = self.from_word_backward(word)
        left = ' '.join(fwb[:-1])
        left = self.adjust_left_line_breaks(left, max_left_line_breaks)
        fwf = self.from_word_forward(word)
        right = ' '.join(fwf[1:])
        right = self.adjust_right_line_breaks(right, max_right_line_breaks)

        # Retain original case/punctuation
        if fwf and self.conv_key(fwf[0]) == self.conv_key(word):
            word = fwf[0]
        elif fwb and self.conv_key(fwb[-1]) == self.conv_key(word):
            word = fwb[-1]

        if max_left_line_breaks is not None:
            left = '\n'.join((left.split('\n')[-max_left_line_breaks-1:]))
        if max_right_line_breaks is not None:
            right = '\n'.join((right.split('\n')[0:max_right_line_breaks+1]))
        if not left and not right:
            return ''
            # Omit first element, which is a duplicate of the word
        return (left + ' ' + word + ' ' + right).replace(' \n ',
            '\n').strip()

    def sentence_from_chain(self, forward_chain, max_left_line_breaks=-1,
            max_right_line_breaks=-1):
        """Generate a full saying from the given chain (in forward order).
        Search for a chain going forward and then complete the sentence by also
        searching backward and combining the pieces."""

        if max_left_line_breaks == -1:
            max_left_line_breaks = self.default_max_left_line_breaks
        if max_right_line_breaks == -1:
            max_right_line_breaks = self.default_max_right_line_breaks

        forward_chain = self.conv_key(forward_chain)
        reverse_chain = tuple(reversed(forward_chain))
        left = ' '.join(self.from_chain_backward(reverse_chain))
        left = self.adjust_left_line_breaks(left, max_left_line_breaks)
        right = ' '.join(self.from_chain_forward(forward_chain)[self._order:])
        right = self.adjust_right_line_breaks(right, max_right_line_breaks)
        if not left and not right:
            return ''
            # Omit first element, which is a duplicate of the word
        result = (left + ' ' + right).strip()
        if result != ' '.join(forward_chain):
            return result.replace(' \n ', '\n')
        return ''


class PostgresMarkov(object):
    """tev's Markov chain implementation using a PostgreSQL backend to store
    the data"""

    def __init__(self, connect, table_name,
            case_sensitive=True,
            ignore_chars=DEFAULT_IGNORE_CHARS):

        self._case_sensitive = case_sensitive
        self._ignore_chars = ignore_chars

        # Set up connection if it's a string; else assume it's a connection
        # object
        self.table_name = table_name
        try:
            self.connection = psycopg2.connect(connect)
        except TypeError:
            self.connection = connect
        self.cursor = self.connection.cursor()
        self.doquery = self.cursor.execute

        # Set up tables if needed
        try:
            self.doquery(
                'CREATE TABLE "{}"'
                '(word VARCHAR,'
                ' next1key VARCHAR DEFAULT NULL, next2key VARCHAR DEFAULT NULL,'
                ' next3key VARCHAR DEFAULT NULL, next4key VARCHAR DEFAULT NULL,'
                ' prev1key VARCHAR DEFAULT NULL, prev2key VARCHAR DEFAULT NULL,'
                ' prev3key VARCHAR DEFAULT NULL, prev4key VARCHAR DEFAULT NULL,'
                ' next1 VARCHAR DEFAULT NULL, next2 VARCHAR DEFAULT NULL,'
                ' next3 VARCHAR DEFAULT NULL, next4 VARCHAR DEFAULT NULL,'
                ' prev1 VARCHAR DEFAULT NULL, prev2 VARCHAR DEFAULT NULL,'
                ' prev3 VARCHAR DEFAULT NULL, '
                ' prev4 VARCHAR DEFAULT NULL)'.format(self.table_name)
            )
        except psycopg2.ProgrammingError:
            self.rollback()
        else:
            self.doquery(
                'CREATE INDEX ON "{}" '
                '(word,next1key,next2key,next3key,next4key)'.format(
                    self.table_name))
            self.doquery(
                'CREATE INDEX ON "{}" '
                '(word,prev1key,prev2key,prev3key,prev4key)'.format(
                    self.table_name))
            self.commit()

    def begin(self):
        self.doquery('BEGIN')

    def commit(self):
        self.doquery('COMMIT')

    def rollback(self):
        self.doquery('ROLLBACK')

    def conv_key(self, s):
        """Convert a string or sequence of strings to lowercase if case
        sensitivity is disabled, and strip characters contained in
        self._ignore_chars.  Non-strings are returned as-is."""
        try:
            s.lower()
        except AttributeError:
            try:
                return [self.conv_key(x) for x in s]
            except TypeError:
                return s
        else:
            if not s:
                return s
            s = re.sub('[{}]'.format(self._ignore_chars), '', s)
            if not self._case_sensitive:
                s = s.lower()
            if s.strip(' '):
                return s
            else:
                return '_'

    def str_to_chain(self, string):
        """Convert a normal sentence in a string to a list of words"""
        return [s for s in string.replace('\n', ' \n ').split(' ') if s]

    def chain_to_str(self, chain):
        """Unsplit a tuple of words back into a string"""
        chain = [s.strip(' ') for s in chain]
        return ' '.join(chain).replace(' \n ', '\n').strip(' ')

    def add(self, sentence):
        """Parse and add a string of words to the chain"""
        words = self.str_to_chain(sentence)
        words = ['']*4 + [x.strip(' ') for x in words] + ['']*4
        for i, word in enumerate(words):
            if not word or i < 4 or i > len(words)-5:
                continue
            forward_chain = words[i+1:i+5]
            backward_chain = words[i-4:i]
            backward_chain.reverse()
            forward_key = self.conv_key(forward_chain)
            backward_key = self.conv_key(backward_chain)
            self.doquery(
                'INSERT INTO "{}" '
                '(word, next1key, next2key, next3key, next4key,'
                ' prev1key, prev2key, prev3key, prev4key,'
                ' next1, next2, next3, next4, prev1, prev2, prev3, prev4) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s, %s,'
                '%s, %s, %s, %s, %s, %s, %s, %s, %s)'.format(self.table_name),
                [self.conv_key(word)] + forward_key + backward_key +
                forward_chain + backward_chain
            )

    def train(self, filename):
        """Train from all lines from the given text file"""
        f = open(filename, 'r')
        for line in f:
            self.add(line)

    def clear(self):
        """Delete all trained data; restart with a completely empty state"""
        self.doquery('DELETE FROM "{}"'.format(self.table_name))

    def adjust_left_line_breaks(self, string, max):
        """Limit newline characters in string to 'max' total, counting from end
        of string backward; truncate any additional newlines and everything
        before them. None for 'max' means unlimited (return string
        unchanged)."""
        if max is not None:
            return '\n'.join(string.split('\n')[-max-1:])
        return string

    def adjust_right_line_breaks(self, string, max):
        """Limit newline characters in string to 'max' total, counting from
        start of string forward; truncate any additional newlines and
        everything after them. None for 'max' means unlimited (return string
        unchanged)."""
        if max is not None:
            return '\n'.join(string.split('\n')[:max+1])
        return string

    def adjust_line_breaks(self, string, lmax, rmax):
        """Limit newline characters in string to 'lmax' total on left side,
        and 'rmax' total on right end."""
        return self.adjust_left_line_breaks(
            self.adjust_right_line_breaks(string, rmax), lmax)

    def forward(self, start):
        """Select and return a chain from the given chain forward in context.
        Input chain is a list/tuple of words one to five items in length."""
        chain = self.conv_key(start)
        chain.reverse()
        q = self.cursor.mogrify(
            'SELECT next1, next2, next3, next4'
            ' FROM "{}" WHERE word=%s'.format(
                self.table_name), (chain[0],))
        if len(chain) >= 2:
            q += self.cursor.mogrify(' AND prev1key=%s', (chain[1],))
        if len(chain) >= 3:
            q += self.cursor.mogrify(' AND prev2key=%s', (chain[2],))
        if len(chain) >= 4:
            q += self.cursor.mogrify(' AND prev3key=%s', (chain[3],))
        if len(chain) >= 5:
            q += self.cursor.mogrify(' AND prev4key=%s', (chain[4],))
        self.doquery(q)
        if not self.cursor.rowcount:
            chain.reverse()     # Back to original order for error message
            raise KeyError("{}: chain not found".format(chain))
        return self.cursor.fetchall()

    def backward(self, start):
        """Select and return a chain from the given chain backward in context.
        Input chain is a list/tuple of words one to five items in length."""
        chain = self.conv_key(start)
        q = self.cursor.mogrify(
            'SELECT prev4, prev3, prev2, prev1'
            ' FROM "{}" WHERE word=%s'.format(
                self.table_name), (chain[0],))
        if len(chain) >= 2:
            q += self.cursor.mogrify(' AND next1key=%s', (chain[1],))
        if len(chain) >= 3:
            q += self.cursor.mogrify(' AND next2key=%s', (chain[2],))
        if len(chain) >= 4:
            q += self.cursor.mogrify(' AND next3key=%s', (chain[3],))
        if len(chain) >= 5:
            q += self.cursor.mogrify(' AND next4key=%s', (chain[4],))
        self.doquery(q)
        if not self.cursor.rowcount:
            raise KeyError("{}: chain not found".format(chain))
        return self.cursor.fetchall()

    def sentence_forward(self, start, length=4):
        """Generate a sentence forward from the start chain.  'length' sets the
        size of the chain used to extend the sentence in words."""
        sentence = tuple(start)
        while True:
            try:
                sentence = sentence + choice(self.forward(sentence[-length:]))
            except KeyError:
                if sentence == tuple(start):
                    raise
                else:
                    break
        return self.chain_to_str(sentence)

    def sentence_backward(self, start, length=4):
        """Generate a sentence backward from the start chain"""
        sentence = tuple(start)
        while True:
            try:
                sentence = choice(self.backward(sentence[:length])) + sentence
            except KeyError:
                if sentence == tuple(start):
                    raise
                else:
                    break
        return self.chain_to_str(sentence)

    def sentence(self, start, forward_length=4, backward_length=4):
        """Generate a full sentence (forward and backward) from the start
        chain, using chain lengths of forward_order (for forward direction) and
        backward_order (for backward direction)."""
        right = self.str_to_chain(self.sentence_forward(start, forward_length))
        back_chain = right[:backward_length]
        left = self.str_to_chain(self.sentence_backward(back_chain,
                                                        backward_length))
        return self.chain_to_str(left[:-len(back_chain)] + \
            list(start) + right[len(start):])

