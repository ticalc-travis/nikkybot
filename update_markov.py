#!/usr/bin/env python2

### IMPORTANT:
# This script will need to be modified to grab the desired lines from whatever
# IRC logs are on hand.  (Mine are all disorganized and in several different
# formats, so this script is longer and more convoluted than would probably
# normally be necessary.)  The lines will be fed to the Markov generator and
# saved in database files under markov/

import os
import re
from sys import stdout, argv, exit

import markov

if len(argv) < 2:
    print "Usage: {} order".format(argv[0])
    exit(1)

order = int(argv[1])
home = os.environ['HOME']
training_glob = []

stdout.write('Starting Markov{} generation.\n'.format(order))
stdout.write('Parsing logs...\n')

# Old Konversation logs
for fn in [os.path.join('log_irc_old', x) for x in
        ('calcgames.log', 'cemetech.log', 'tcpa.log', 'ti.log',
            'efnet_#tiasm.log')]:
    with open(os.path.join(home, fn), 'r') as f:
        line_group = []
        for line in f:
            line = line.strip()
            m = re.match(r'^\[.*\] \[.*\] <(nikky|allyn).*?>\t(.*)', line, re.I)
            if m:
                line_group.append(m.group(2))
            else:
                if line_group:
                    training_glob.append('\n'.join(line_group))
                line_group = []

# Newer irssi logs
log_path = os.path.join(home, os.path.join('log_irc_new'))
for dn in [os.path.join(log_path, x) for x in os.listdir(log_path)]:
    try:
        for fn in os.listdir(dn):
            if fn.split('_2')[0] in ('#calcgames', '#cemetech', '#flood', '#hp48',
                    '#inspired', '#nspire-lua', '#prizm', '#tcpa', '#ti'):
                with open(os.path.join(log_path, os.path.join(dn, fn)), 'r') as f:
                    line_group = []
                    for line in f:
                        line = line.strip()
                        m = re.match('^[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} (<[ @+](nikky(?!(?:bot|test)).*?|allyn.*?)>|<[ @+]saxjax> \(.\) \[allynfolksjr\]) (.*)', line, re.I)
                        if m:
                            line_group.append(m.group(3))
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
                m = re.match(r'^\[[0-9]{2}:[0-9]{2}:[0-9]{2}\] <.?(nikky|allyn).*?> (.*)', line, re.I)
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
            m = re.match(r'^[0-9]{2}:[0-9]{2}:[0-9]{2} <.?(nikky|allyn).*?> (.*)', line, re.I)
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
        m = re.match(r'^\[?[0-9]{2}:[0-9]{2}(:[0-9]{2})?\]? <.?(nikky|allyn).*?> (.*)', line, re.I)
        if m:
            line_group.append(m.group(3))
        else:
            if line_group:
                training_glob.append('\n'.join(line_group))
            line_group = []

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

# There, that's all I have
#   ...I think...

items = len(training_glob)
m = markov.Markov(order, case_sensitive=False)
for i, l in enumerate(training_glob):
    if not (i+1) % 100 or i+1 == items:
        stdout.write('Training {}/{}...\r'.format(i+1, items))
        stdout.flush()
    m.add(l)

stdout.write('\nWriting shelves...\n')
s = markov.Markov_Shelved('markov/new.nikky-markov.{}'.format(order), readonly=False,
    order=order, case_sensitive=False)
for src, dst in ((m.word_forward, s.word_forward),
             (m.word_backward, s.word_backward),
             (m.chain_forward, s.chain_forward),
             (m.chain_backward, s.chain_backward)):
    keys = src.keys()
    n = len(keys)
    for i, k in enumerate(keys):
        if not (i+1) % 100 or i+1 == n:
            stdout.write('    Key {}/{}...\r'.format(i+1, n))
            stdout.flush()
        dst[k] = src[k]
    stdout.write('\n')

stdout.write('Closing...\n')
s.sync()
s.close()
stdout.write('Finished!\n\n')
