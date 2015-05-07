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
DEFAULT_CONTEXT_IGNORE_WORDS = (
'\n', '_', 'nikkybot',
'a', 'about', 'above', 'after', 'again', 'against', 'ah', 'all', 'also',
'am', 'an', 'and', 'any', 'anything', 'are', 'as', 'at', 'back', 'be', 'been',
'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can', 'cant',
'come', 'could', 'did', 'didnt', 'do', 'does', 'doesnt', 'doing', 'dont',
'down', 'during', 'each', 'even', 'ever', 'else', 'everything', 'few', 'first',
'for', 'from', 'further', 'get', 'getting', 'give', 'go', 'goes', 'going',
'good', 'got', 'had', 'has', 'have', 'havent', 'having', 'he', 'hello', 'her',
'here', 'hers', 'herself', 'hi', 'him', 'himself', 'his', 'how', 'i', 'id',
'if', 'ill', 'im', 'in', 'into', 'is', 'it', 'its', 'itself', 'just', 'know',
'like', 'look', 'make', 'me', 'more', 'most', 'much', 'my', 'myself', 'new',
'no', 'nor', 'not', 'now', 'of', 'off', 'ok', 'okay', 'on', 'once', 'one',
'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out', 'over', 'own',
'people', 'same', 'say', 'see', 'she', 'should', 'since', 'so', 'some',
'something', 'such', 'take', 'than', 'that', 'thatd', 'thats', 'the', 'their',
'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they', 'thing',
'think', 'this', 'those', 'though', 'through', 'to', 'too', 'two', 'under',
'until', 'up', 'us', 'use', 'very', 'want', 'was', 'way', 'we', 'well', 'were',
'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'will',
'with', 'work', 'would', 'yeah', 'yes', 'yep', 'you', 'your', 'yours',
'yourself', 'yourselves',
)
DEFAULT_CONTEXT_IGNORE_PREFIXES = (
're', 'un',
)
DEFAULT_CONTEXT_IGNORE_SUFFIXES = (
's', 'est', 'es', 'ies', 'ion', 'er', 'en', 'ed', 'ly', 'y', 'ing', 'ings',
't', 've', 're', 'd', 'm',
)

class PostgresMarkov(object):
    """tev's Markov chain implementation using a PostgreSQL backend to store
    the data"""

    def __init__(self, connect, table_name,
            case_sensitive=True,
            ignore_chars=DEFAULT_IGNORE_CHARS,
            ignore_words=DEFAULT_CONTEXT_IGNORE_WORDS,
            ignore_prefixes=DEFAULT_CONTEXT_IGNORE_PREFIXES,
            ignore_suffixes=DEFAULT_CONTEXT_IGNORE_SUFFIXES):

        self.case_sensitive = case_sensitive
        self.ignore_chars = ignore_chars
        self.ignore_words = [self.conv_key(w) for w in ignore_words]
        self.ignore_prefixes = ignore_prefixes
        self.ignore_suffixes = ignore_suffixes

        # Set up connection if it's a string; else assume it's a connection
        # object
        self.table_name = table_name
        self.context_table_name = table_name + '.context'
        try:
            self.connection = psycopg2.connect(connect)
        except TypeError:
            self.connection = connect
        self.cursor = self.connection.cursor()

        # Set up tables if needed

        # Markov
        try:
            self.doquery(
                'CREATE TABLE "{}"'
                ' (word VARCHAR, rawword VARCHAR,'
                ' next1key VARCHAR DEFAULT NULL,'
                ' next2key VARCHAR DEFAULT NULL,'
                ' next3key VARCHAR DEFAULT NULL,'
                ' next4key VARCHAR DEFAULT NULL,'
                ' prev1key VARCHAR DEFAULT NULL,'
                ' prev2key VARCHAR DEFAULT NULL,'
                ' prev3key VARCHAR DEFAULT NULL,'
                ' prev4key VARCHAR DEFAULT NULL,'
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

        # Context
        try:
            self.doquery(
                'CREATE TABLE "{}"'
                ' (inword VARCHAR NOT NULL, outword VARCHAR NOT NULL,'
                '  freq INTEGER DEFAULT 1 CHECK (freq > 0) NOT NULL,'
                '  UNIQUE (inword, outword))'.format(
                    self.context_table_name)
            )
        except psycopg2.ProgrammingError:
            self.rollback()
        else:
            self.doquery(
                'CREATE INDEX ON "{}" (outword, inword)'.format(
                    self.context_table_name))
            self.commit()

    def doquery(self, querystr, args=None):
        if args is None:
            new_args = None
        else:
            new_args = []
            for a in args:
                try:
                    new_args.append(unicode(a, encoding='utf8',
                                            errors='replace'))
                except TypeError:
                    new_args.append(a)
        return self.cursor.execute(querystr, new_args)

    def begin(self):
        self.doquery('BEGIN')

    def commit(self):
        self.doquery('COMMIT')

    def rollback(self):
        self.doquery('ROLLBACK')

    def conv_key(self, s):
        """Convert a string or sequence of strings to lowercase if case
        sensitivity is disabled, and strip characters contained in
        self.ignore_chars.  Non-strings are returned as-is."""
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
            s = re.sub('[{}]'.format(self.ignore_chars), '', s)
            if not self.case_sensitive:
                s = s.lower()
            if s.strip(' '):
                return s
            else:
                return '_'

    def normalize_word(self, word):
        """Normalize a word for context checking--convert to lowercase, strip
        characters in self.ignore_chars, and remove common word suffixes."""
        word = self.conv_key(word)
        remove = ''
        for r in self.ignore_prefixes:
            r = r.lower()
            if word.endswith(r) and len(r) > len(remove):
                remove = r
        if remove:
            word = word[len(remove):]
        for r in self.ignore_suffixes:
            r = r.lower()
            if word.endswith(r) and len(r) > len(remove):
                remove = r
        if remove:
            word = word[:-len(remove)]
        return word

    def str_to_chain(self, string, wildcard=None):
        """Convert a normal sentence in a string to a list of words.
        If 'wildcard' is a string, replace words matching that string with the
        object None."""
        chain = []
        for s in string.replace('\n', ' \n ').split(' '):
            if s == wildcard:
                chain.append(None)
            elif s:
                chain.append(s)
        return chain

    def chain_to_str(self, chain):
        """Unsplit a tuple of words back into a string"""
        chain = [s.strip(' ') for s in chain]
        return ' '.join(chain).replace(' \n ', '\n').strip(' ')

    def add(self, sentence, context=None):
        """Parse and add a string of words to the chain; update context
        information from 'context' string if given"""
        words = self.str_to_chain(sentence)
        words = ['']*4 + [x.strip(' ') for x in words] + ['']*4
        context_words = self.str_to_chain(context) if context else []
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
                '(word, rawword, next1key, next2key, next3key, next4key,'
                ' prev1key, prev2key, prev3key, prev4key,'
                ' next1, next2, next3, next4, prev1, prev2, prev3, prev4) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,'
                '%s, %s, %s, %s, %s, %s, %s, %s, %s)'.format(self.table_name),
                [self.conv_key(word), word] + forward_key + backward_key +
                forward_chain + backward_chain
            )
            # Update context/relevance table if context is provided
            for cword in context_words:
                self.add_context(cword, word)

    def train(self, filename):
        """Train from all lines from the given text file"""
        f = open(filename, 'r')
        for line in f:
            self.add(line)

    def add_context(self, in_word, out_word):
        """Associate in_word with out_word, keeping track of frequency of
        associations, to estimate relative relation between the two words."""

        if (self.conv_key(in_word) in self.ignore_words or
                self.conv_key(out_word) in self.ignore_words):
            return
        in_word, out_word = (self.normalize_word(in_word),
                             self.normalize_word(out_word))
        if not in_word or not out_word:
            return
        # Don't record information for generic words
        self.doquery(
            'SELECT * FROM "{}" WHERE inword=%s AND outword=%s'.format(
                self.context_table_name),
            (in_word, out_word))
        if not self.cursor.rowcount:
            # Add new entry
            self.doquery(
                'INSERT INTO "{}" (inword, outword) VALUES'
                ' (%s, %s)'.format(self.context_table_name),
                (in_word, out_word))
        else:
            # Increment frequency of existing entry
            self.doquery(
                'UPDATE "{}" SET freq = freq + 1 WHERE'
                ' inword=%s AND outword=%s'.format(self.context_table_name),
                (in_word, out_word))

    def get_context_freq(self, in_word, out_word):
        """Return number of times in_word was associated with out_word in
        context."""
        in_word, out_word = (self.normalize_word(in_word),
                             self.normalize_word(out_word))
        self.doquery(
            'SELECT freq FROM "{}" WHERE inword=%s AND outword=%s'.format(
                self.context_table_name),
            (in_word, out_word))
        if self.cursor.rowcount:
            return self.cursor.fetchone()[0]
        else:
            return 0

    def get_context_score(self, output_candidate, context):
        """Scores the relevance of words in 'output_candidate' string to the
        words in the 'context' string based on trained context information."""
        in_words = [self.normalize_word(w) for w in self.str_to_chain(context)]
        out_words = [self.normalize_word(w) for w in
                     self.str_to_chain(output_candidate)]
        score = count = 0
        for ow in out_words:
            for iw in in_words:
                score += self.get_context_freq(iw, ow)
                count += 1
        return score / float(count) if count else 0.

    def clear(self):
        """Delete all trained data and context; restart with a completely empty
        state"""
        self.doquery('DELETE FROM "{}"'.format(self.table_name))
        self.doquery('DELETE FROM "{}"'.format(self.context_table_name))

    def forward(self, start):
        """Return a list of available chains from the given chain forward in
        context.  Input chain is a list/tuple of words one to five items in
        length.  None objects may be given to serve as "wildcards" for
        particular word positions.  Output is a list of pairs of chains, the
        first in the pair covering the given context from 'start' (with
        wildcards filled in), the second covering the next words in context
        after 'start'.
        """
        chain = tuple(start)
        chain = self.conv_key(start)
        chain.reverse()
        if len(chain) < 1 or len(chain) > 5:
            raise IndexError("'start' must contain 1 to 5 items")
        if not [x for x in chain if x is not None]:
            raise ValueError("'start' must contain at least one non-None item")

        # Gather a list of columns backward in context to cover length of
        # given chain
        context_cols = ['rawword','prev1','prev2','prev3','prev4'][:len(chain)]
        context_cols.reverse()
        context_cols = ', '.join(context_cols)

        q1 = 'SELECT {}, next1, next2, next3, next4 FROM "{}" WHERE '.format(
            context_cols, self.table_name)
        q2 = []
        if chain[0] is not None:
            q2.append(self.cursor.mogrify('word=%s', (chain[0],)))
        if len(chain) >= 2 and chain[1] is not None:
            q2.append(self.cursor.mogrify('prev1key=%s', (chain[1],)))
        if len(chain) >= 3 and chain[2] is not None:
            q2.append(self.cursor.mogrify('prev2key=%s', (chain[2],)))
        if len(chain) >= 4 and chain[3] is not None:
            q2.append(self.cursor.mogrify('prev3key=%s', (chain[3],)))
        if len(chain) >= 5 and chain[4] is not None:
            q2.append(self.cursor.mogrify('prev4key=%s', (chain[4],)))
        q = q1 + ' AND '.join(q2)
        self.doquery(q)
        if not self.cursor.rowcount:
            chain.reverse()     # Back to original order for error message
            raise KeyError("{}: chain not found".format(chain))
        return [(t[:len(chain)], t[len(chain):]) for t in
                self.cursor.fetchall()]

    def backward(self, start):
        """Return a list of available chains from the given chain backward in
        context.  Input chain is a list/tuple of words one to five items in
        length.  None objects may be given to serve as "wildcards" for
        particular word positions.  Output is a list of pairs of chains, the
        first in the pair covering the given context from 'start' (with
        wildcards filled in), the second covering the previous words in context
        before 'start'.
        """
        chain = tuple(start)
        chain = self.conv_key(start)
        if len(chain) < 1 or len(chain) > 5:
            raise IndexError("'start' must contain 1 to 5 items")
        if not [x for x in chain if x is not None]:
            raise ValueError("'start' must contain at least one non-None item")

        # Gather a list of columns forward in context to cover length of
        # given chain
        context_cols = ['rawword','next1','next2','next3','next4'][:len(chain)]
        context_cols = ', '.join(context_cols)

        q1 = 'SELECT {}, prev4, prev3, prev2, prev1 FROM "{}" WHERE '.format(
            context_cols, self.table_name)
        q2 = []
        if chain[0] is not None:
            q2.append(self.cursor.mogrify('word=%s', (chain[0],)))
        if len(chain) >= 2 and chain[1] is not None:
            q2.append(self.cursor.mogrify('next1key=%s', (chain[1],)))
        if len(chain) >= 3 and chain[2] is not None:
            q2.append(self.cursor.mogrify('next2key=%s', (chain[2],)))
        if len(chain) >= 4 and chain[3] is not None:
            q2.append(self.cursor.mogrify('next3key=%s', (chain[3],)))
        if len(chain) >= 5 and chain[4] is not None:
            q2.append(self.cursor.mogrify('next4key=%s', (chain[4],)))
        q = q1 + ' AND '.join(q2)
        self.doquery(q)
        if not self.cursor.rowcount:
            raise KeyError("{}: chain not found".format(chain))
        return [(t[:len(chain)], t[len(chain):]) for t in
                self.cursor.fetchall()]

    def _filter_completions(self, sentence, completions,
                            allow_empty_completion, max_lf,
                            backwards=False):
        # Truncate each completion starting with a line break that exceeds the
        # maximum number of allowed line breaks (line breaks already in
        # 'sentence' chain are counted toward this total).  Then remove each
        # empty completion if not allow_empty_completion (including those that
        # end up empty due to line break truncation).
        choices = []
        for c in completions:
            c = list(c)
            lf_count = sentence.count('\n')
            if backwards:
                c.reverse()
            for i, word in enumerate(c):
                if word == '\n':
                    lf_count += 1
                if max_lf is not None and lf_count > max_lf:
                    c[i] = ''
            if backwards:
                c.reverse()
            if allow_empty_completion or c != ['', '', '', '']:
                choices.append(tuple(c))
        return choices

    def sentence_forward(self, start, length=4, allow_empty_completion=True,
                         max_lf=None):
        """Generate a sentence forward from the start chain.
        length:  Size of the chain used to extend the sentence in words
        allow_empty_completion:  If False, do not return a chain identical
          to the start chain, but always a non-empty chain completion (return
          KeyError if this is not possible).
        max_lf:  Limit number of line breaks in output sentence to this value
          (None = unlimited)
        """
        sentence = start = choice(self.forward(start))[0]
        while True:
            try:
                choices = [t[1] for t in self.forward(sentence[-length:])]
                choices = self._filter_completions(
                    sentence, choices, allow_empty_completion, max_lf)
                        # Handle line length limits and empty completions
                # If nothing to choose, raise end-of-chain KeyError; handle it
                # in the exception handler below
                if not choices:
                    raise KeyError(
                        'No non-empty forward chain completion for: ' +
                        repr(start))
                sentence = sentence + choice(choices)[:length]
            except KeyError:
                # End of chain--if anything was added to 'start', quit and
                # return result; otherwise re-raise the exception
                if sentence == start:
                    raise
                else:
                    break
        return self.chain_to_str(sentence)

    def sentence_backward(self, start, length=4, allow_empty_completion=True,
                          max_lf=None):
        """Generate a sentence backward from the start chain.
        length:  Size of the chain used to extend the sentence in words
        allow_empty_completion:  If False, do not return a chain identical
          to the start chain, but always a non-empty chain completion (return
          KeyError if this is not possible).
        max_lf:  Limit number of line breaks in output sentence to this value
          (None = unlimited)
        """
        sentence = start = choice(self.backward(start))[0]
        while True:
            try:
                choices = [t[1] for t in self.backward(sentence[:length])]
                choices = self._filter_completions(
                    sentence, choices, allow_empty_completion, max_lf,
                    backwards=True)
                        # Handle line length limits and empty completions
                # If nothing to choose, raise end-of-chain KeyError; handle it
                # in the exception handler below
                if not choices:
                    # If that leaves us with nothing to choose, raise the
                    # end-of-chain KeyError; handle it in the exception
                    # handler below
                    raise KeyError(
                        'No non-empty backward chain completion for: ' +
                        repr(start))
                sentence = choice(choices)[-length:] + sentence
            except KeyError:
                # End of chain--if anything was added to 'start', quit and
                # return result; otherwise re-raise the exception
                if sentence == start:
                    raise
                else:
                    break
        return self.chain_to_str(sentence)

    def sentence(self, start, forward_length=4, backward_length=4,
                 max_lf_forward=None, max_lf_backward=None):
        """Generate a full sentence (forward and backward) from the start
        chain, using chain lengths of forward_length (for forward direction)
        and backward_length (for backward direction).  Limit number of line
        breaks to max_lf_forward and max_lf_backward (None = unlimited)"""
        right = self.str_to_chain(
            self.sentence_forward(start, forward_length, max_lf=max_lf_forward))
        back_chain = right[:backward_length]
        left = self.str_to_chain(
            self.sentence_backward(back_chain, backward_length,
                                   max_lf=max_lf_backward))
        return self.chain_to_str(left[:-len(back_chain)] + right)
