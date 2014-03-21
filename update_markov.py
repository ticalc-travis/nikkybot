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
    cur.execute('CREATE TABLE IF NOT EXISTS ".last-updated" (name VARCHAR PRIMARY KEY, updated TIMESTAMP NOT NULL DEFAULT NOW())')
    cur.execute('SELECT updated FROM ".last-updated" WHERE name=%s', (table_name,))
    target_date = datetime(year=datetime.now().year,
                        month=datetime.now().month,
                        day=datetime.now().day)
    if not reset and cur.rowcount:
        last_updated = cur.fetchone()[0]
        last_updated = datetime(year=last_updated.year,
                                month=last_updated.month,
                                day=last_updated.day)
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
        
        last_updated = NEVER_UPDATED

        # Parse old logs this first time only

        # Old Konversation logs
        for fn in [os.path.join('log_irc_old', x) for x in
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
        log_path = os.path.join('/home/retrotcpa', os.path.join('log_irc_retro'))
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
        log_path = os.path.join('/home/retrotcpa', os.path.join('log_calcgames'))
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

        # More miscellaneous junk I threw in a separate huge file because it was
        # too scattered around my system
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
                        
    # Current irssi logs
    stdout.write('Parsing current logs...\n')
    log_path = os.path.join(home, os.path.join('log_irc_new'))
    for dn in [os.path.join(log_path, x) for x in sorted(os.listdir(log_path))]:
        try:
            for fn in sorted(os.listdir(dn)):
                m = re.match('#(.*)_([0-9]{4})-([0-9]{2})-([0-9]{2})\.log', fn)
                if m:
                    channel, year, month, day = m.groups()
                    log_date = datetime(
                        year=int(year), month=int(month), day=int(day))
                    if (channel in 
                            ('calcgames', 'cemetech', 'flood', 'hp48',
                            'inspired', 'nspire-lua', 'prizm', 'tcpa', 'ti')
                            and log_date < target_date
                            and last_updated <= log_date):
                        with open(os.path.join(log_path, dn, fn), 'r') as f:
                            #stdout.write('Parsing {}...\n'.format(fn))
                            line_group = []
                            for line in f:
                                line = line.strip()
                                m = re.match(r'^[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} <[ @+]?'+pregex[0]+'> (.*)',line, re.I)
                                if not m and pregex[1]:
                                    m = re.match(r'^[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} <[ @+]?saxjax> \(.\) \[?'+pregex[1]+r'[:\]] (.*)', line, re.I)
                                    if not m and pregex[2]:
                                        m = re.match(r'^[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} <[ @+]?omnomirc.?> (?:\(.\))?<'+pregex[2]+r'> (.*)', line, re.I)
                                if m:
                                    line_group.append(m.group(2))
                                else:
                                    if line_group:
                                        training_glob.append('\n'.join(line_group))
                                    line_group = []
        except OSError as e:
            if e.errno == 20:
                pass
            else:
                raise e

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

