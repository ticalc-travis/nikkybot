#!/usr/bin/env python2

import argparse
from datetime import datetime
import os
import re
from sys import stdout, stderr, exit

import psycopg2

import markov
from personalitiesrc import personality_regexes


class BadPersonalityError(KeyError):
    pass


def print_line(nick, text):
    stdout.write('<%s> %s\n' % (nick, text))


def print_context_break():
    stdout.write('\n')


def output_corpus(pname, reset, update_datestamp):
    NEVER_UPDATED = datetime(1970, 1, 1, 0, 0)
    home = os.environ['HOME']
    try:
        pregex = personality_regexes[pname]
    except KeyError:
        raise BadPersonalityError

    stderr.write('Starting {} corpus search.\n'.format(pname))

    # Get last updated date
    conn = psycopg2.connect('dbname=markovmix user=markovmix')
    mk = markov.PostgresMarkov(conn, pname, case_sensitive=False)
    mk.begin()
    mk.doquery('CREATE TABLE IF NOT EXISTS ".last-updated" '
        '(name VARCHAR PRIMARY KEY, updated TIMESTAMP NOT NULL DEFAULT NOW())')
    mk.doquery('SELECT updated FROM ".last-updated" WHERE name=%s', (pname,))
    target_date = datetime.now()
    if not reset and mk.cursor.rowcount:
        last_updated = mk.cursor.fetchone()[0]
    else:
        last_updated = NEVER_UPDATED

    # Updated last updated date if enabled (will only be written to DB
    # if entire process finishes to the commit call at the end of the
    # function)
    if update_datestamp:
        mk.doquery(
            'UPDATE ".last-updated" SET updated = NOW() WHERE name=%s', (pname,))
        if not mk.cursor.rowcount:
            mk.doquery('INSERT INTO ".last-updated" VALUES (%s)', (pname,))
    else:
        stderr.write('Skipping datestamp update.\n')

    if reset:

        ## Never updated yet ##
        stderr.write('Parsing old logs...\n')

        # Parse old logs this first time only

        # Old Konversation logs
        for fn in [os.path.join('log_irc_konversation', x) for x in
                ('calcgames.log', 'cemetech.log', 'tcpa.log', 'ti.log',
                'efnet_#tiasm.log', 'omnimaga.log')]:
            with open(os.path.join(home, fn), 'r') as f:
                for line in f:
                    line = line.strip()
                    m = re.match(r'^\[.*\] \[.*\] <saxjax>\t\(.\) \[?(.*?)[:\]] (.*)', line, re.I)
                    if not m:
                        m = re.match(r'^\[.*\] \[.*\] <(.*?)>\t(.*)', line, re.I)
                    if m:
                        print_line(m.group(1), m.group(2))
            print_context_break()

        # Old #tcpa logs from elsewhere
        log_path = os.path.join('/home/tcparetro',
                                os.path.join('log_irc_retro'))
        for dn in [os.path.join(log_path, x) for x in sorted(
                os.listdir(log_path))]:
            for fn in sorted(os.listdir(dn)):
                with open(os.path.join(log_path, os.path.join(dn, fn)),
                          'r') as f:
                    for line in f:
                        line = line.strip()
                        m = re.match(r'^\[[0-9]{2}:[0-9]{2}:[0-9]{2}\] <[ @+]?(.*?)> (.*)', line, re.I)
                        if m:
                            print_line(m.group(1), m.group(2))
        print_context_break()

        # Old #calcgames logs from elsewhere
        log_path = os.path.join('/home/tcparetro',
                                os.path.join('log_calcgames'))
        for fn in sorted(os.listdir(log_path)):
            with open(os.path.join(log_path, fn), 'r') as f:
                for line in f:
                    line = line.strip()
                    m = re.match(r'^[0-9]{2}:[0-9]{2}:[0-9]{2} <[ @+]?(.*?)> (.*)', line, re.I)
                    if m:
                        print_line(m.group(1), m.group(2))
        print_context_break()

        # More miscellaneous junk I threw in a separate huge file because it
        # was too scattered around my system
        with open('misc_irc_lines.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if pregex[1]:
                    m = re.match(r'^\[?[0-9]{2}:[0-9]{2}(:[0-9]{2})?\]? <[ @+]?saxjax> (.*?): (.*)', line, re.I)
                if not m:
                    m = re.match(r'^\[?[0-9]{2}:[0-9]{2}(:[0-9]{2})?\]? <[ @+]?(.*?)> (.*)', line, re.I)
                if m:
                    print_line(m.group(2), m.group(3))
        print_context_break()

        # Stuff from elsewhere or not in my logs that I wanted to add
        log_path = [os.path.join('manual_corpus', x) for x in
                    os.listdir('manual_corpus') if
                    x.endswith('.txt') and not x.startswith('.') and not
                    x.startswith('#')]
        for fn in log_path:
            with open(fn, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        m = re.match(r'^<(.*?)> (.*)', line, re.I)
                        if m:
                            print_line(m.group(1), m.group(2))
                    else:
                        print_context_break()
            print_context_break()

        # irssi logs
        log_path = os.path.join(home, os.path.join('log_irc_irssi'))
        for dn in [os.path.join(log_path, x) for x in os.listdir(log_path)]:
            try:
                last_channel = None
                for fn in sorted(os.listdir(dn)):
                    fm = re.match(
                        '#(.*)_([0-9]{4})-([0-9]{2})-([0-9]{2})\.log', fn)
                    if fm:
                        channel, year, month, day = fm.groups()
                        if (channel in
                                ('calcgames', 'cemetech', 'flood', 'hp48',
                                'inspired', 'nspire-lua', 'prizm', 'tcpa',
                                'ti', 'caleb', 'wikiti', 'markov')):
                            if channel != last_channel:
                                print_context_break()
                                last_channel = channel
                            with open(os.path.join(log_path, dn, fn), 'r') as f:
                                for line in f:
                                    line = line.strip()
                                    m = re.match(r'^[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} <[ @+]?saxjax> \(.\) \[?(.*?)[:\]] (.*)', line, re.I)
                                    if not m:
                                        m = re.match(r'^[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} <[ @+]?omnomirc.?> (?:\(.\))?<(.*?)> (.*)', line, re.I)
                                    if not m:
                                        m = re.match(r'^[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} <[ @+]?(.*?)> (.*)', line, re.I)
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

                                        print_line(nick, msg)

            except OSError as e:
                if e.errno == 20:
                    continue
        print_context_break()

    # Parse current weechat logs
    stderr.write('Parsing current logs...\n')
    for fn in [os.path.join('log_irc_weechat', 'irc.efnet.#'+x+'.weechatlog')
               for x in
            ('calcgames', 'cemetech', 'tcpa', 'ti', 'omnimaga', 'flood',
             'caleb', 'caleb-spam', 'hp48', 'markov', 'nspired', 'nspire-lua',
             'prizm', 'wikiti', 'cemetech-mc', 'codewalrus', 'gbadev',
             'kinginfinity')]:
        with open(os.path.join(home, fn), 'r') as f:
            for line in f:
                line = line.strip()

                m1 = re.match(r'^([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})\t[+@]?(.*?)\t(.*)', line)
                m2 = re.match(r'^(..., [0-9]{2} ... [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}) [-+][0-9]{4}\t[+@]?(.*?)\t(.*)', line)
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
                if (nick.lower().startswith('saxjax') or
                        nick.lower().startswith('cemetecmc')):
                    m = re.match(r'^\(.\) \[?(.*?)[:\]] (.*)', msg, re.I)
                    if not m:
                        m = re.match(r'^(?:\(.\) )?(?:[[*](.*?)[]]?) (.*)',
                                     msg, re.I)
                elif nick.lower().startswith('omnomnirc'):
                    m = re.match(r'^(?:\(.\))?<(.*?)> (.*)', msg, re.I)
                elif (nick.lower().startswith('walriibot') or
                      nick.lower().startswith('wb') or
                      nick.lower().startswith('i|') or
                      nick.lower().startswith('l|') or
                      nick.lower().startswith('j|') or
                      nick.lower().startswith('yukitg')):
                    m = re.match(r'^(?:\(.*?\))?<(.*?)> (.*)', msg, re.I)
                else:
                    m = None
                if m:
                    nick, msg = m.group(1), m.group(2)
                print_line(nick, msg)
        print_context_break()

    mk.commit()
    conn.close()
    stderr.write('Finished!\n\n')


def get_arg_parser():
    parser = argparse.ArgumentParser(
        description='Output updated corpus lines for piping to train.py')
    parser.add_argument('personality', nargs=1,
                        help='name of the personality to train')
    parser.add_argument('-r', '--reset', action='store_true',
                        help='clear last updated datestamp and output an entire corpus from the beginning')
    parser.add_argument('-n', '--no-update-datestamp', action='store_true',
                        help='do not update the last-updated datestamp upon completion; leave it alone')
    return parser


if __name__ == '__main__':
    args = get_arg_parser().parse_args()
    pname = args.personality[0]
    reset = args.reset
    update_datestamp = not args.no_update_datestamp

    try:
        output_corpus(pname, reset, update_datestamp)
    except BadPersonalityError:
        print "Personality '{}' not defined in personalitiesrc.py".format(pname)
        exit(2)
