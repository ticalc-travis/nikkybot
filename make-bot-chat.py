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

NUMBER_OF_ROUNDS = 50

import textwrap
from sys import argv, exit
from time import sleep

import nikkyai
import personalitiesrc

# Work around Python2's stupid encoding nonsense
import sys
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout, 'replace')
def just_PRINT_DAMNIT(s):
    print(s.decode(encoding='utf-8', errors='replace'))

def usage_exit():
    print('Usage: {} personality1 personality2'.format(argv[0]))
    print('\n\nPersonalities:\n')
    print(', '.join(sorted(personalities)))
    exit(2)

personalities = personalitiesrc.personalities

if len(argv) != 3:
    usage_exit()
nick1, nick2 = argv[1], argv[2]
if nick1 != 'nikky' and nick1 not in personalities:
    usage_exit()
elif nick2 != 'nikky' and nick2 not in personalities:
    usage_exit()

if nick1 == nick2:
    tag1, tag2 = '1', '2'
else:
    tag1 = tag2 = None

bot1 = nikkyai.NikkyAI(recurse_limit=10, debug=False, max_lf_l=10, max_lf_r=10,
                       personality=nick1, id='*botchat*', search_time=.1)
bot2 = nikkyai.NikkyAI(recurse_limit=10, debug=False, max_lf_l=10, max_lf_r=10,
                       personality=nick2, id='*botchat*', search_time=.1)

tw = textwrap.TextWrapper(subsequent_indent=' '*20, expand_tabs=True, width=80)

def get_response(bot, nick, target_nick, msg):
    msg = '<{}> {}'.format(target_nick, msg)
    reply = bot.reply(msg)
    return reply

def format_response(nick, msg, tag=None):
    msg = msg.split('\n')
    if nick == 'nikky':
        display_nick = nick + 'bot'
    else:
        display_nick = nick + '-bot'
    if tag is not None:
        display_nick = display_nick + '-' + tag
    formatted_msg = []
    for line in msg:
        if line.startswith('\x01ACTION ') and line.endswith('\x01'):
            line = line[8:-1]
            tw.initial_indent = ' * {} '.format(display_nick)
        else:
            tw.initial_indent = '{:<20}'.format('<' + display_nick + '>')
        formatted_msg.append(tw.fill(line))
    formatted_msg = '\n'.join(formatted_msg)
    return formatted_msg

response = ''
for i in xrange(NUMBER_OF_ROUNDS):
    response = get_response(bot1, nick1, nick2, response)
    just_PRINT_DAMNIT(format_response(nick1, response, tag1) + '\n')
    response = get_response(bot2, nick2, nick1, response)
    just_PRINT_DAMNIT(format_response(nick2, response, tag2) + '\n')
