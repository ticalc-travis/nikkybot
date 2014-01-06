#!/usr/bin/env python2

from __future__ import print_function

import nikkyai
import markovmixai
import textwrap
from sys import argv, exit
from time import sleep

NUMBER_OF_ROUNDS = 50
nikkyai.DEBUG = False
nikkyai.RECURSE_LIMIT = 333
markovmixai.DEBUG = False
markovmixai.RECURSE_LIMIT = 333

def usage_exit():
    print('Usage: {} personality1 personality2'.format(argv[0]))
    print('\n\nPersonalities:\n')
    print(', '.join(['nikkybot'] + sorted(personalities)))
    exit(1)

personalities = markovmixai.get_personalities()

if len(argv) != 3:
    usage_exit()
nick1, nick2 = argv[1], argv[2]
if nick1 != 'nikkybot' and nick1 not in personalities:
    usage_exit()
elif nick2 != 'nikkybot' and nick2 not in personalities:
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
    msg = '<' + target_nick + '> ' + msg
    if nick == 'nikkybot':
        reply = nikkybot.reply(msg)
    else:
        reply = markovmix.reply('?' + nick + ' ' + msg)
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
    print(format_response(nick1, response, tag1)+'\n')
    response = get_response(nick2, nick1, response)
    print(format_response(nick2, response, tag2)+'\n')
