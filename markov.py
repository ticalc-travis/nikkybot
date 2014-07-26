# -*- coding: utf-8 -*-

# Simple Markov chain implementation
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

from random import choice
import re
import psycopg2

DEFAULT_IGNORE_CHARS = '\\]\\-!"&`()*,./:;<=>?[\\^=\'{|}~_'

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
        """Return a list of available chains from the given chain forward in
        context.  Input chain is a list/tuple of words one to five items in
        length."""
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
        """Return a list of available chains from the given chain backward in
        context.  Input chain is a list/tuple of words one to five items in length."""
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

    def sentence_forward(self, start, length=4, allow_empty_completion=True):
        """Generate a sentence forward from the start chain.  'length' sets the
        size of the chain used to extend the sentence in words.
        If 'allow_empty_completion' is False, do not return a chain identical
        to the start chain, but always a non-empty chain completion (return
        KeyError if this is not possible)."""
        sentence = tuple(start)
        while True:
            try:
                choices = self.forward(sentence[-length:])
                if not allow_empty_completion:
                    choices = [c for c in choices if c != ('', '', '', '')]
                    if not choices:
                        raise KeyError('No non-empty forward chain completion for: ' + repr(start))
                sentence = sentence + choice(choices)
            except KeyError:
                if sentence == tuple(start):
                    raise
                else:
                    break
        return self.chain_to_str(sentence)

    def sentence_backward(self, start, length=4, allow_empty_completion=True):
        """Generate a sentence backward from the start chain.  'length' sets
        the size of the chain used to extend the sentence in words.
        If 'allow_empty_completion' is False, do not return a chain identical
        to the start chain, but always a non-empty chain completion (return
        KeyError if this is not possible)."""
        sentence = tuple(start)
        while True:
            try:
                choices = self.backward(sentence[:length])
                if not allow_empty_completion:
                    choices = [c for c in choices if c != ('', '', '', '')]
                    if not choices:
                        raise KeyError('No non-empty backward chain completion for: ' + repr(start))
                sentence = choice(choices) + sentence
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

