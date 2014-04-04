#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# “NikkyBot”
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

from __future__ import print_function

import nikkyai
import markovmixai
import textwrap
from sys import argv, exit
from time import sleep

# Work around Python2's stupid encoding nonsense
import sys
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout, 'replace')
def just_PRINT_DAMNIT(s):
    print(s.decode(errors='replace'))

NUMBER_OF_ROUNDS = 50
nikkyai.DEBUG = False
nikkyai.RECURSE_LIMIT = 10
nikkyai.MAX_LF_L = 10
nikkyai.MAX_LF_R = 10
markovmixai.DEBUG = False
markovmixai.RECURSE_LIMIT = 10
markovmixai.MAX_LF_L = 10
markovmixai.MAX_LF_R = 10

def usage_exit():
    print('Usage: {} personality1 personality2'.format(argv[0]))
    print('\n\nPersonalities:\n')
    print(', '.join(['nikkybot'] + sorted(personalities)))
    exit(1)

personalities = markovmixai.PERSONALITIES

if len(argv) != 3:
    usage_exit()
nick1, nick2 = argv[1], argv[2]
if nick1 not in ('nikkybot', 'nikky') and nick1 not in personalities:
    usage_exit()
elif nick2 not in ('nikkybot', 'nikky') and nick2 not in personalities:
    usage_exit()
    
if nick1 == nick2:
    tag1, tag2 = '1', '2'
else:
    tag1 = tag2 = None

nikkybot = nikkyai.NikkyAI()
nikkybot.load_preferred_keywords()
markovmix = markovmixai.NikkyAI()
markovmix.load_preferred_keywords()

tw = textwrap.TextWrapper(subsequent_indent=' '*20, expand_tabs=True, width=80)

def get_response(nick, target_nick, msg):
    if isinstance(msg, list):
        msg = '\n'.join(msg)
    if nick in ('nikky', 'nikkybot'):
        msg = '<' + target_nick + '> ' + msg
        reply = nikkybot.reply(msg)
    else:
        reply = markovmix.reply('<' + target_nick + '> ?' + nick + ' ' + msg)
        reply = [line.replace('<' + nick + '> ', '', 1) for line in reply]
    if not isinstance(reply, list):
        reply = [reply]
    return reply

def format_response(nick, msg, tag=None):
    if nick == 'nikkybot':
        display_nick = nick
    else:
        display_nick = nick + '-bot'
    if tag is not None:
        display_nick = display_nick + '-' + tag
    tw.initial_indent='{:<20}'.format('<' + display_nick + '>')
    msg = [tw.fill(p) for p in msg]
    msg = '\n'.join(msg)
    return msg

response = 'Hi'
for i in xrange(NUMBER_OF_ROUNDS):
    response = get_response(nick1, nick2, response)
    just_PRINT_DAMNIT(format_response(nick1, response, tag1) + '\n')
    response = get_response(nick2, nick1, response)
    just_PRINT_DAMNIT(format_response(nick2, response, tag2) + '\n')
