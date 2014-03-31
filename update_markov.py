#!/usr/bin/env python2

### IMPORTANT:
# This script will need to be modified to grab the desired lines from whatever
# IRC logs are on hand.  (Mine are all disorganized and in several different
# formats, so this script is longer and more convoluted than would probably
# normally be necessary.)  The lines will be fed to the Markov generator and
# saved in database files under markov/

import os
import re
from datetime import datetime
from sys import stdout, argv, exit
import psycopg2

import markov
from personalitiesrc import personality_regexes

class BadPersonalityError(KeyError):
    pass

def update(pname, reset):
    NEVER_UPDATED = datetime(1970, 1, 1, 0, 0)
    home = os.environ['HOME']
    training_glob = []
    table_name = '{}'.format(pname)
    try:
        pregex = personality_regexes[pname]
    except KeyError:
        raise UpdateError

    stdout.write('Starting {} Markov generation.\n'.format(table_name))

    # Get last updated date
    conn = psycopg2.connect('dbname=markovmix user=markovmix')
    mk = markov.PostgresMarkov(conn, '{}'.format(pname), case_sensitive=False)
    mk.begin()
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS ".last-updated" '
        '(name VARCHAR PRIMARY KEY, updated TIMESTAMP NOT NULL DEFAULT NOW())')
    cur.execute('SELECT updated FROM ".last-updated" WHERE name=%s',
                (table_name,))
    target_date = datetime.now()
    if not reset and cur.rowcount:
        last_updated = cur.fetchone()[0]
    else:
        last_updated = NEVER_UPDATED
    # Updated last updated date (will only be written to DB if entire process
    # finishes to the commit call at the end of the script)
    cur.execute('UPDATE ".last-updated" SET updated = NOW() WHERE name=%s',
                (table_name,))
    if not cur.rowcount:
        cur.execute('INSERT INTO ".last-updated" VALUES (%s)', (table_name,))

    if last_updated == NEVER_UPDATED:

        ## Never updated yet ##
        stdout.write('Parsing old logs...\n')

        # Parse old logs this first time only

        # Old Konversation logs
        for fn in [os.path.join('log_irc_konversation', x) for x in
                ('calcgames.log', 'cemetech.log', 'tcpa.log', 'ti.log',
                'efnet_#tiasm.log', 'omnimaga.log')]:
            with open(os.path.join(home, fn), 'r') as f:
                line_group = []
                for line in f:
                    line = line.strip()
                    m = re.match(r'^\[.*\] \[.*\] <'+pregex[0]+r'>\t(.*)',
                                line, re.I)
                    if not m and pregex[1]:
                        m = re.match(r'^\[.*\] \[.*\] <saxjax>\t\(.\) \[?'+pregex[1]+r'[:\]] (.*)', line, re.I)
                    if m:
                        line_group.append(m.group(2))
                    else:
                        if line_group:
                            training_glob.append('\n'.join(line_group))
                        line_group = []

        # Old #tcpa logs from elsewhere
        log_path = os.path.join('/home/retrotcpa',
                                os.path.join('log_irc_retro'))
        for dn in [os.path.join(log_path, x) for x in os.listdir(log_path)]:
            for fn in os.listdir(dn):
                with open(os.path.join(log_path, os.path.join(dn, fn)), 'r') as f:
                    line_group = []
                    for line in f:
                        line = line.strip()
                        m = re.match(r'^\[[0-9]{2}:[0-9]{2}:[0-9]{2}\] <[ @+]?'+pregex[0]+'> (.*)', line, re.I)
                        if m:
                            line_group.append(m.group(2))
                        else:
                            if line_group:
                                training_glob.append('\n'.join(line_group))
                            line_group = []

        # Old #calcgames logs from elsewhere
        log_path = os.path.join('/home/retrotcpa',
                                os.path.join('log_calcgames'))
        for fn in os.listdir(log_path):
            with open(os.path.join(log_path, fn), 'r') as f:
                line_group = []
                for line in f:
                    line = line.strip()
                    m = re.match(r'^[0-9]{2}:[0-9]{2}:[0-9]{2} <[ @+]?'+pregex[0]+'> (.*)', line, re.I)
                    if m:
                        line_group.append(m.group(2))
                    else:
                        if line_group:
                            training_glob.append('\n'.join(line_group))
                        line_group = []

        # More miscellaneous junk I threw in a separate huge file because it
        # was too scattered around my system
        with open('misc_irc_lines.txt', 'r') as f:
            line_group = []
            for line in f:
                line = line.strip()
                m = re.match(r'^\[?[0-9]{2}:[0-9]{2}(:[0-9]{2})?\]? <[ @+]?'+pregex[0]+'> (.*)', line, re.I)
                if m:
                    line_group.append(m.group(3))
                else:
                    if line_group:
                        training_glob.append('\n'.join(line_group))
                    line_group = []

        if pname == 'nikky':
            # !TODO! Generalize this
            # And some stuff from elsewhere, too!
            with open('manually-added.txt', 'r') as f:
                line_group = []
                for line in f:
                    line = line.strip()
                    if re.match(r'(.+)', line, re.I):
                        line_group.append(line)
                    else:
                        if line_group:
                            training_glob.append('\n'.join(line_group))
                        line_group = []

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
                                line_group = []
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

                                        if re.match('^'+pregex[0]+'$', nick):
                                            line_group.append(msg)
                                            continue

                                    if pregex[1]:
                                        m = re.match(r'^[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} <[ @+]?saxjax> \(.\) \[?'+pregex[1]+r'[:\]] (.*)', line, re.I)
                                        if m:
                                            line_group.append(m.group(2))
                                        elif pregex[2]:
                                            m = re.match(r'^[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} <[ @+]?omnomirc.?> (?:\(.\))?<'+pregex[2]+r'> (.*)', line, re.I)
                                            if m:
                                                line_group.append(m.group(2))
                                    if not m:
                                        if line_group:
                                            training_glob.append('\n'.join(line_group))
                                        line_group = []
            except OSError as e:
                if e.errno == 20:
                    continue

    # Parse current weechat logs
    stdout.write('Parsing current logs...\n')
    for fn in [os.path.join('log_irc_weechat', 'irc.efnet.#'+x+'.weechatlog')
               for x in
            ('calcgames', 'cemetech', 'tcpa', 'ti', 'omnimaga', 'flood',
             'caleb', 'hp48', 'markov', 'nspired', 'nspire-lua', 'prizm',
             'wikiti')]:
        with open(os.path.join(home, fn), 'r') as f:
            line_group = []
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
                # !TODO! Add a date cutoff here when this mess is finally over
                #   with
                if nick.lower().startswith('nikkybot'):
                    nick = 'nikky'
                elif nick.lower().startswith('nikky'):
                    nick = 'nikkybot'

                if date < last_updated or date > target_date:
                    continue
                if re.match('^'+pregex[0]+'$', nick, re.I):
                    line_group.append(msg)
                elif pregex[1] and nick.lower().startswith('saxjax'):
                    m = re.match(r'^\(.\) \[?'+pregex[1]+r'[:\]] (.*)',
                                 msg, re.I)
                    if m:
                        line_group.append(m.group(2))
                elif pregex[2] and nick.lower().startswith('omnomnirc'):
                    m = re.match(r'^(?:\(.\))?<'+pregex[2]+r'> (.*)',
                                 msg, re.I)
                    if m:
                        line_group.append(m.group(2))
                else:
                    if line_group:
                        training_glob.append('\n'.join(line_group))
                    line_group = []

    items = len(training_glob)
    if last_updated == NEVER_UPDATED:
        mk.clear()
    for i, l in enumerate(training_glob):
        stdout.write('Training {}/{}...\r'.format(i+1, items))
        stdout.flush()
        mk.add(unicode(l, errors='replace'))

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

