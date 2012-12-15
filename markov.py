#!/usr/bin/env python3

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

from collections import defaultdict
from random import choice

class Markov:
    """tev's Markov chain implementation"""
    
    def __init__(self, order=2, case_sensitive=True):
        self._order = order
        self._case_sensitive = case_sensitive
        self.word_forward = defaultdict(list)
        self.chain_forward = defaultdict(list)
        self.word_backward = defaultdict(list)
        self.chain_backward = defaultdict(list)
        
    def conv_case(self, s):
        """Convert a string or sequence of strings to lowercase if case
        sensitivity is disabled"""
        if self._case_sensitive:
            return s
        try:
            return s.lower()
        except AttributeError:
            return [x.lower() for x in s]
        
    def _add(self, words, word_dict, chain_dict):
        for i, word in enumerate(words):
            order = self._order
            chain = words[i:i+self._order+1]
            chain = tuple(chain)
            word_value = chain[:order]
            word_key = self.conv_case(word)
            chain_value = chain[1:order+1]
            chain_key = tuple(self.conv_case(chain[:order]))
            if not word_value in word_dict[word_key]:
                word_dict[word_key].append(word_value)
            if not chain_value in chain_dict[chain_key]:
                chain_dict[chain_key].append(chain_value)
        
    def add(self, sentence):
        """Parse and add a string of words to the chain"""
        words = sentence.split()
        self._add(words, self.word_forward, self.chain_forward)
        words.reverse()
        self._add(words, self.word_backward, self.chain_backward)
        
    def train(self, filename):
        """Train from all lines from the given text file"""
        f = open(filename, 'r', errors='ignore')
        for line in f:
            self.add(line)
            
    def get_chain_forward(self, chain):
        """Select and return a chain from the given chain forward in context"""
        try:
            return choice(self.chain_forward[tuple(self.conv_case(chain))])
        except IndexError:
            return ()
        
    def get_chain_backward(self, chain):
        """Select and return a chain from the given chain backward in context"""
        try:
            return choice(self.chain_backward[tuple(self.conv_case(chain))])
        except IndexError:
            return ()
        
    def from_chain_forward(self, chain):
        """Generate a chain from the given chain forward in context"""
        out = list(chain)
        while chain:
            chain = self.get_chain_forward(chain)
            try:
                out.append(chain[self._order-1])
            except IndexError:
                pass
        return out
        
    def from_chain_backward(self, chain):
        """Generate a chain from the given chain backward in context"""
        out = list(chain)
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
            chain = choice(self.word_forward[self.conv_case(word)])
        except IndexError:
            return ()
        return self.from_chain_forward(chain)
        
    def from_word_backward(self, word):
        """Generate a chain from the given word backward in context"""
        try:
            chain = choice(self.word_backward[self.conv_case(word)])
        except IndexError:
            return ()
        return self.from_chain_backward(chain)
        
    def sentence_from_word(self, word):
        """Generate a full saying from the given word.  Search for a
        chain going forward and then complete the sentence by also searching
        backward and combining the pieces."""
        left = ' '.join(self.from_word_backward(word)[:-1])
        right = ' '.join(self.from_word_forward(word)[1:])
        if not left and not right:
            return ''
            # Omit first element, which is a duplicate of the word
        return (left + ' ' + word + ' ' + right).strip()
        
    def sentence_from_chain(self, forward_chain):
        """Generate a full saying from the given chain (in forward order). 
        Search for a chain going forward and then complete the sentence by also
        searching backward and combining the pieces."""
        reverse_chain = tuple(reversed(forward_chain))
        left = ' '.join(self.from_chain_backward(reverse_chain))
        right = ' '.join(self.from_chain_forward(forward_chain)[self._order:])
        if not left and not right:
            return ''
            # Omit first element, which is a duplicate of the word
        result = (left + ' ' + right).strip()
        if result != ' '.join(forward_chain):
            return result
        return ''



#m = Markov(order=4, case_sensitive=False)
#m.train('test.trn')
#import pickle
#f = open('nikky-markov.4.pickle', 'rb')
#m = pickle.load(f)
#f.close()
