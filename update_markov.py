#!/usr/bin/env python2

### IMPORTANT:
# This script will need to be modified to grab the desired lines from whatever
# IRC logs are on hand.  (Mine are all disorganized and in several different
# formats, so this script is longer and more convulted than would probably
# normally be necessary.)  They will be saved to 'nikkybot.trn' and then fed to
# the Markov generator.

import cPickle
import os
import re
from sys import stdout

import markov

home = os.environ['HOME']
training_glob = []

stdout.write('Parsing logs...\n')

# Old Konversation logs
for fn in [os.path.join('log_irc_old', x) for x in
        ('calcgames.log', 'cemetech.log', 'tcpa.log', 'ti.log',
            'efnet_#tiasm.log')]:
    with open(os.path.join(home, fn), 'r') as f:
        line_group = []
        for line in f:
            line = line.strip()
            m = re.match(r'\[.*\] \[.*\] <nikky>\t(.*)', line, re.I)
            if m:
                line_group.append(m.group(1))
            else:
                if line_group:
                    training_glob.append('\n'.join(line_group))
                line_group = []

# Newer irssi logs
log_path = os.path.join(home, os.path.join('log_irc_new'))
for dn in [os.path.join(log_path, x) for x in os.listdir(log_path)]:
    try:
        for fn in os.listdir(dn):
            if fn.split('_')[0] in ('#calcgames', '#cemetech', '#flood', '#hp48',
                    '#inspired', '#nspire-lua', '#prizm', '#tcpa', '#ti'):
                with open(os.path.join(log_path, os.path.join(dn, fn)), 'r') as f:
                    line_group = []
                    for line in f:
                        line = line.strip()
                        m = re.match(r'[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} <.(nikky|nikky_|nikky_s|nikkyjr|nikky_jr|nikkylap|nikkydesk|nikkyserv|nikkycat|nikkyirss|)> (.*)', line, re.I)
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

# Old #tcpa logs from elsewhere
log_path = os.path.join('/home/retrotcpa', os.path.join('log_irc_retro'))
for dn in [os.path.join(log_path, x) for x in os.listdir(log_path)]:
    for fn in os.listdir(dn):
        with open(os.path.join(log_path, os.path.join(dn, fn)), 'r') as f:
            line_group = []
            for line in f:
                line = line.strip()
                m = re.match(r'\[[0-9]{2}:[0-9]{2}:[0-9]{2}\] <.?nikky.*> (.*)', line, re.I)
                if m:
                    line_group.append(m.group(1))
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
            m = re.match(r'[0-9]{2}:[0-9]{2}:[0-9]{2} <.?nikky.*> (.*)', line, re.I)
            if m:
                line_group.append(m.group(1))
            else:
                if line_group:
                    training_glob.append('\n'.join(line_group))
                line_group = []

# There, that's all I have
#   ...I think...

# Update pickle dumps
for order in (2, 3, 4, 5):
    items = len(training_glob)
    stdout.write('Markov{} pickle:\n'.format(order))
    fn = 'nikky-markov.{}.pickle.new'.format(order)
    with open(fn, 'wb') as f:
        m = markov.Markov(order, case_sensitive=False)
        for i, l in enumerate(training_glob):
            if not (i+1) % 1000 or i+1 == items:
                stdout.write('    Training {}/{}...\r'.format(i, items))
                stdout.flush()
            m.add(l)
        stdout.write('\n    Writing...\n')
        cPickle.dump(m, f, protocol=2)
        del m

stdout.write('Finished!\n')
