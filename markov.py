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

from collections import defaultdict, Counter
from random import choice, randint
import re
import shelve

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


class Markov_Shelf(shelve.DbfilenameShelf):
    """Compatibility layer for Markov classes' use of dicts"""

    def __getitem__(self, key):
        try:
            return shelve.Shelf.__getitem__(self, repr(key))
        except KeyError:
            return Counter()

    def __setitem__(self, key, value):
        shelve.Shelf.__setitem__(self, repr(key), value)

    def has_key(self, key):
        return shelve.Shelf.has_key(self, repr(key))

    def keys(self):
        return [eval(x) for x in shelve.Shelf.keys(self)]

    def random_key(self):
        return choice(self.keys())


class Markov_Shelved(Markov):
    """Markov chain using shelf module for less RAM usage"""

    def __init__(self, file_prefix, readonly=False, order=2, case_sensitive=True,
            ignore_chars=DEFAULT_IGNORE_CHARS,
            default_max_left_line_breaks=None, default_max_right_line_breaks=None):
        self._order = order
        self._case_sensitive = case_sensitive
        self._ignore_chars = ignore_chars
        self.default_max_left_line_breaks = None
        self.default_max_right_line_breaks = None

        flag = 'c'
        if readonly:
            flag = 'r'

        self.word_forward = \
            Markov_Shelf(file_prefix + '.wf', protocol=2, flag=flag,
                writeback=False)
        self.chain_forward = \
            Markov_Shelf(file_prefix + '.cf', protocol=2, flag=flag,
                writeback=False)
        self.word_backward = \
            Markov_Shelf(file_prefix + '.wb', protocol=2, flag=flag,
                writeback=False)
        self.chain_backward = \
            Markov_Shelf(file_prefix + '.cb', protocol=2, flag=flag,
                writeback=False)

    def sync(self):
        self.word_forward.sync()
        self.chain_forward.sync()
        self.word_backward.sync()
        self.chain_backward.sync()

    def close(self):
        self.word_forward.close()
        self.chain_forward.close()
        self.word_backward.close()
        self.chain_backward.close()

