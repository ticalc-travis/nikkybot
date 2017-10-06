#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Number of previous spoken IRC lines to include in Markov context data
CONTEXT_LINES = 5
# Context-scoring relevance weight for lines highlighting personality
CONTEXT_HIGHLIGHT_BIAS = 100
# Frequency to update the progress indicator
PROGRESS_EVERY = 5000

import argparse
import os
import re
from collections import deque, Counter
from datetime import datetime
from sys import stdin, stdout, exit
import psycopg2

import markov
from personalitiesrc import personality_regexes


# TODO: All the raw SQL query stuff (and likely the whole TrainingCorpus
# object itself) really ought to be part of the markov.PostgresMarkov
# class. All the DB internals should be abstracted away so that one can
# create versions of this class that use other backends and have them still
# work.


class TrainingCorpus(object):
    """An object for preparing Markov corpus data for insertion into the
    database.
    """

    def __init__(self, nick_regexes, markov, context_lines=CONTEXT_LINES):
        """nick_regexes:  A sequence of regular expressions matching the
        nickname of this corpus's Markov personality

        markov:  The markov.PostgresMarkov object that the corpus will
        train

        context_lines:  The number of lines of context, before and after
        each group of spoken lines trained, to use for context data
        """
        self.nick_regexes = nick_regexes
        self.context_group = deque([], maxlen=context_lines)
        self.spoken_group = []
        self._corpus = []
        self._context = Counter()
        self.markov = markov

    def is_nick(self, search):
        """Return whether the given search string matches one of the
        personality's nicks, as indicated by self.nick_regexes.
        """
        for regex in self.nick_regexes:
            if regex and re.match(regex, search, re.I):
                return True
        return False

    def add_spoken(self, line):
        """Train “line” as a spoken line, whose data will be added to the
        personality's Markov database.
        """
        self.spoken_group.append(line)

    def add_context(self, line):
        """Train “line” as a contextual (non-spoken) line to be added to
        the personality's non-spoken context data.
        """
        self._update()
        self.context_group.append(line)

    def check_line(self, nick, line):
        """Check if “line”, spoken by “nick”, is a line spoken by the
        personality being trained (i.e., “nick” matches one of the
        personality's nicks according to nick_regexes passed to
        self.__init__). If so, train the line as a spoken line by
        calling self.add_spoken(line), else train it as a context line
        by calling self.add_context(line).
        """
        nick = unicode(nick, encoding='utf8', errors='replace')
        line = unicode(line, encoding='utf8', errors='replace')
        if self.is_nick(nick):
            self.add_spoken(line)
        else:
            self.add_context(line)

    def _update_context(self):
        """Called internally by self._update. This should not be used directly."""
        spoken = self.markov.str_to_chain('\n'.join(self.spoken_group))
        for cline in self.context_group:
            bias = CONTEXT_HIGHLIGHT_BIAS if self.is_nick(cline) else 1
            context = self.markov.str_to_chain(cline)
            for cword in context:
                for sword in spoken:
                    t = self.markov.normalize_context(cword, sword)
                    if t:
                        in_word, out_word = t
                        self._context[(in_word, out_word)] += bias

    def _update(self):
        """Update internal state and prepare for a new group of spoken
        lines. This method is an implementation detail and should not be
        used directly outside of this class.
        """
        if self.spoken_group:
            self._corpus.append('\n'.join(self.spoken_group))
            self._update_context()
            self.spoken_group = []
            self.context_group.clear()

    def new_context(self):
        """Signal that subsequent lines passed to self.check_line(),
        self.add_spoken(), or self.add_context() for training are
        contextually unrelated to the last group of lines processed and
        should be kept separate in the context data.
        """
        self._update()
        self.context_group.clear()

    def markov_rows(self, limit=PROGRESS_EVERY):
        """Return a set of rows of trained Markov data which can be passed to
        markov.PostgresMarkov.add_markov_rows()
        """
        self._update()
        rows = []
        n = len(self._corpus)
        for i, group in enumerate(self._corpus):
            rows += self.markov.make_markov_rows(group)
            if len(rows) >= limit:
                yield (i, n), rows[:limit]
                rows = rows[limit:]
        if rows:
            yield (n, n), rows
        raise StopIteration

    def context_rows(self, limit=PROGRESS_EVERY):
        """Return a set of rows of trained context data which can be passed to
        markov.PostgresMarkov.add_context()
        """
        self._update()
        rows = []
        i, n = 0, len(self._context)
        for word_pair, freq in self._context.items():
            rows.append((word_pair[0], word_pair[1], freq))
            i += 1
            if len(rows) == limit:
                yield (i, n), rows
                rows = []
        if rows:
            yield (n, n), rows
        raise StopIteration


class BadPersonalityError(KeyError):
    pass


def update(pname, reset, infile):
    try:
        pregex = personality_regexes[pname]
    except KeyError:
        raise BadPersonalityError

    stdout.write('Starting {} Markov generation.\n'.format(pname))

    conn = psycopg2.connect('dbname=markovmix user=markovmix')
    mk = markov.PostgresMarkov(conn, pname, case_sensitive=False)
    corpus = TrainingCorpus(pregex, mk)

    mk.begin()

    for line in infile:
        line = line.strip()
        if line:
            m = re.match(r'^<(.*?)> ?(.*)', line, re.I)
            if m:
                corpus.check_line(m.group(1), m.group(2))
        else:
            corpus.new_context()

    if reset:
        mk.clear()

    # Write Markov data
    if reset:
        stdout.write('Reinitializing tables...\n')
        mk.doquery('DROP TABLE IF EXISTS ".markov.old"')
        mk.doquery('DROP TABLE IF EXISTS ".context.old"')
        mk.doquery('ALTER TABLE "{}" RENAME TO ".markov.old"'.format(
            mk.table_name))
        mk.doquery('ALTER TABLE "{}" RENAME TO ".context.old"'.format(
            mk.context_table_name))
        mk.create_tables()

    for progress, rows in corpus.markov_rows():
        mk.add_markov_rows(rows)
        stdout.write('Inserting Markov data {}/{}...\r'.format(
            progress[0], progress[1]))
        stdout.flush()
    stdout.write('\n')

    # Write context data
    for progress, rows in corpus.context_rows(PROGRESS_EVERY if reset else 1):
        if reset:
            mk.cursor.executemany(
                'INSERT INTO "{}" (inword, outword, freq) VALUES'
                ' (%s, %s, %s)'.format(mk.context_table_name), rows)
        else:
            inword, outword, freq = rows[0]
            mk.add_context(inword, outword, freq)
        stdout.write('Inserting context data {}/{}...\r'.format(
            progress[0], progress[1]))
        stdout.flush()

    stdout.write('\n')
    if reset:
        stdout.write('Indexing tables...\n')
        mk.index_tables()

    stdout.write('Closing...\n')
    mk.commit()
    conn.close()
    stdout.write('Finished!\n\n')


def get_arg_parser():
    parser = argparse.ArgumentParser(
        description='Train a NikkyBot personality with text from stdin',
        epilog='Input text is read from standard input.'
        ' Each line should be in the form “<speaking-nick> spoken text”.'
        ' Blank lines denote breaks in conversation context.')
    parser.add_argument('personality', nargs=1,
                        help='name of the personality to train')
    parser.add_argument('-r', '--reset', action='store_true',
                        help='delete all existing training data before training')
    return parser


if __name__ == '__main__':
    args = get_arg_parser().parse_args()
    pname, reset = args.personality[0], args.reset

    try:
        update(pname, reset, stdin)
    except BadPersonalityError:
        print "Personality '{}' not defined in personalitiesrc.py".format(pname)
        exit(2)
