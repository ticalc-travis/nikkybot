#!/usr/bin/env python2

### IMPORTANT:
# This script will need to be modified to grab the desired lines from whatever
# IRC logs are on hand.  (Mine are all disorganized and in several different
# formats, so this script is longer and more convoluted than would probably
# normally be necessary.)  The lines will be processed and used to populate the
# Markov and relevance/context data in the database.

# Number of previous spoken IRC lines to include in Markov context data
CONTEXT_LINES = 10

import os
import re
from collections import deque
from datetime import datetime
from sys import stdout, argv, exit
import psycopg2

import markov
from personalitiesrc import personality_regexes

class TrainingCorpus(object):
    def __init__(self, nick_regexes, context_lines=CONTEXT_LINES):
        self.nick_regexes = nick_regexes
        self.context_group = deque([], maxlen=context_lines)
        self.spoken_group = []
        self._corpus = []

    def check_line(self, nick, line):
        m = None
        for regex in self.nick_regexes:
            if regex:
                m = re.match(regex, nick, re.I)
                if m:
                    break
        if m:
            self.add_spoken(line)
        else:
            self.add_context(line)

    def add_spoken(self, line):
        self.spoken_group.append(line)

    def add_context(self, line):
        self.update()
        self.context_group.append(line)

    def update(self):
        if self.spoken_group:
            self._corpus.append(
                ('\n'.join(self.spoken_group),
                 '\n'.join(self.context_group))
            )
            self.spoken_group = []
        self.context_group.clear()

    def get_corpus(self):
        self.update()
        return self._corpus

class BadPersonalityError(KeyError):
    pass

def update(pname, reset):
    NEVER_UPDATED = datetime(1970, 1, 1, 0, 0)
    home = os.environ['HOME']
    try:
        pregex = personality_regexes[pname]
    except KeyError:
        raise BadPersonalityError

    stdout.write('Starting {} Markov generation.\n'.format(pname))

    # Get last updated date
    conn = psycopg2.connect('dbname=markovmix user=markovmix')
    mk = markov.PostgresMarkov(conn, '{}'.format(pname), case_sensitive=False)
    mk.begin()
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS ".last-updated" '
        '(name VARCHAR PRIMARY KEY, updated TIMESTAMP NOT NULL DEFAULT NOW())')
    cur.execute('SELECT updated FROM ".last-updated" WHERE name=%s',
                (pname,))
    target_date = datetime.now()
    if not reset and cur.rowcount:
        last_updated = cur.fetchone()[0]
    else:
        last_updated = NEVER_UPDATED
    # Updated last updated date (will only be written to DB if entire process
    # finishes to the commit call at the end of the script)
    cur.execute('UPDATE ".last-updated" SET updated = NOW() WHERE name=%s',
                (pname,))
    if not cur.rowcount:
        cur.execute('INSERT INTO ".last-updated" VALUES (%s)', (pname,))

    corpus = TrainingCorpus(pregex)

    if last_updated == NEVER_UPDATED:

        ## Never updated yet ##
        stdout.write('Parsing old logs...\n')

        # Parse old logs this first time only

        # Old Konversation logs
        for fn in [os.path.join('log_irc_konversation', x) for x in
                ('calcgames.log', 'cemetech.log', 'tcpa.log', 'ti.log',
                'efnet_#tiasm.log', 'omnimaga.log')]:
            with open(os.path.join(home, fn), 'r') as f:
                for line in f:
                    line = line.strip()
                    m = re.match(r'^\[.*\] \[.*\] <(.*?)>\t(.*)',
                                 line, re.I)
                    if not m and pregex[1]:
                        m = re.match(r'^\[.*\] \[.*\] <saxjax>\t\(.\) \[?(.*?)[:\]] (.*)', line, re.I)
                    if m:
                        corpus.check_line(m.group(1), m.group(2))
            corpus.update()

        # Old #tcpa logs from elsewhere
        log_path = os.path.join('/home/retrotcpa',
                                os.path.join('log_irc_retro'))
        for dn in [os.path.join(log_path, x) for x in os.listdir(log_path)]:
            for fn in os.listdir(dn):
                with open(os.path.join(log_path, os.path.join(dn, fn)),
                          'r') as f:
                    for line in f:
                        line = line.strip()
                        m = re.match(r'^\[[0-9]{2}:[0-9]{2}:[0-9]{2}\] <[ @+]?(.*?)> (.*)', line, re.I)
                        if m:
                            corpus.check_line(m.group(1), m.group(2))
            corpus.update()

        # Old #calcgames logs from elsewhere
        log_path = os.path.join('/home/retrotcpa',
                                os.path.join('log_calcgames'))
        for fn in os.listdir(log_path):
            with open(os.path.join(log_path, fn), 'r') as f:
                for line in f:
                    line = line.strip()
                    m = re.match(r'^[0-9]{2}:[0-9]{2}:[0-9]{2} <[ @+]?(.*?)> (.*)', line, re.I)
                    if m:
                        corpus.check_line(m.group(1), m.group(2))
            corpus.update()

        # More miscellaneous junk I threw in a separate huge file because it
        # was too scattered around my system
        with open('misc_irc_lines.txt', 'r') as f:
            for line in f:
                line = line.strip()
                m = re.match(r'^\[?[0-9]{2}:[0-9]{2}(:[0-9]{2})?\]? <[ @+]?(.*?)> (.*)', line, re.I)
                if m:
                    corpus.check_line(m.group(2), m.group(3))

        if pname == 'nikky':
            # !TODO! Generalize this
            # And some stuff from elsewhere, too!
            with open('manually-added.txt', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        corpus.add_spoken(line)
                    else:
                        corpus.update()

        # irssi logs
        log_path = os.path.join(home, os.path.join('log_irc_irssi'))
        for dn in [os.path.join(log_path, x) for x in os.listdir(log_path)]:
            try:
                for fn in os.listdir(dn):
                    m = re.match('#(.*)_([0-9]{4})-([0-9]{2})-([0-9]{2})\.log', fn)
                    if m:
                        channel, year, month, day = m.groups()
                        if (channel in
                                ('calcgames', 'cemetech', 'flood', 'hp48',
                                'inspired', 'nspire-lua', 'prizm', 'tcpa',
                                'ti', 'caleb', 'wikiti', 'markov')):
                            with open(os.path.join(log_path, dn, fn), 'r') as f:
                                for line in f:
                                    line = line.strip()
                                    m = re.match(r'^[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} <[ @+]?(.*)> (.*)', line, re.I)
                                    if m:
                                        nick, msg = m.groups()

                                        # Special case to handle our silly
                                        # nikky/nikkybot nick-swapping stunt
                                        if datetime(year=int(year),
                                                    month=int(month),
                                                    day=int(day)) >= datetime(2014, 3, 9):
                                            if nick.lower().startswith('nikkybot'):
                                                nick = 'nikky'
                                            elif nick.lower().startswith('nikky'):
                                                nick = 'nikkybot'

                                        corpus.check_line(nick, msg)

                                    if pregex[1]:
                                        m = re.match(r'^[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} <[ @+]?saxjax> \(.\) \[?(.*?)[:\]] (.*)', line, re.I)
                                        if m:
                                            corpus.check_line(m.group(1),
                                                              m.group(2))
                                        elif pregex[2]:
                                            m = re.match(r'^[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} <[ @+]?omnomirc.?> (?:\(.\))?<(.*?)> (.*)', line, re.I)
                                            if m:
                                                corpus.check_line(m.group(1),
                                                                  m.group(2))
                    corpus.update()

            except OSError as e:
                if e.errno == 20:
                    continue

    # Parse current weechat logs
    stdout.write('Parsing current logs...\n')
    for fn in [os.path.join('log_irc_weechat', 'irc.efnet.#'+x+'.weechatlog')
               for x in
            ('calcgames', 'cemetech', 'tcpa', 'ti', 'omnimaga', 'flood',
             'caleb', 'caleb-spam', 'hp48', 'markov', 'nspired', 'nspire-lua',
             'prizm', 'wikiti', 'cemetech-mc', 'codewalrus')]:
        with open(os.path.join(home, fn), 'r') as f:
            for line in f:
                line = line.strip()
                m1 = re.match(r'^([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})\t[+@]?(.*)\t(.*)', line)
                m2 = re.match(r'^(..., [0-9]{2} ... [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}) [-+][0-9]{4}\t[+@]?(.*)\t(.*)', line)
                if m1:
                    date, nick, msg = m1.groups()
                    date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                elif m2:
                    date, nick, msg = m2.groups()
                    date = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S')
                else:
                    continue

                # Special case to handle our silly nikky/nikkybot nick-swapping
                #   stunt
                if date < datetime(year=2014, month=5, day=2):
                    if nick.lower().startswith('nikkybot'):
                        nick = 'nikky'
                    elif nick.lower().startswith('nikky'):
                        nick = 'nikkybot'

                if date < last_updated or date > target_date:
                    continue
                # TODO: Need to parse WalriiBot messages
                if pregex[1] and (nick.lower().startswith('saxjax') or
                                  nick.lower().startswith('cemetecmc')):
                    m = re.match(r'^\(.\) \[?(.*?)[:\]] (.*)', msg, re.I)
                elif pregex[2] and nick.lower().startswith('omnomnirc'):
                    m = re.match(r'^(?:\(.\))?<(.*?)> (.*)', msg, re.I)
                else:
                    m = None
                if m:
                    nick, msg = m.group(1), m.group(2)
                corpus.check_line(nick, msg)
        corpus.update()

    c = corpus.get_corpus()
    num_items = len(c)
    if last_updated == NEVER_UPDATED:
        mk.clear()
    for i, citem in enumerate(c):
        stdout.write('Training {}/{}...\r'.format(i+1, num_items))
        stdout.flush()
        spoken, context = citem
        mk.add(spoken, context)
    stdout.write('\nClosing...\n')
    mk.commit()
    stdout.write('Finished!\n\n')

if __name__ == '__main__':
    if len(argv) < 2:
        print "Usage: {} nick [RESET]".format(argv[0])
        exit(1)

    reset = False
    try:
        if argv[2] == 'RESET':
            reset = True
    except IndexError:
        pass
    pname = argv[1]

    try:
        update(pname, reset)
    except BadPersonalityError:
        print "Personality '{}' not defined in personalitiesrc.py".format(pname)
        exit(2)

