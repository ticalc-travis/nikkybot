#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# “NikkyBot”
# Copyright ©2012-2016 Travis Evans
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

from collections import defaultdict
from collections import deque

import argparse
import cPickle
import random
import time
import sys

from twisted.python.rebuild import rebuild
from twisted.internet import reactor, protocol
from twisted.python import log

import nikkybot
import nikkyai

OPTS = argparse.Namespace()
CONTEXT_LINES = 5

class DefaultNikkyAIDict(dict):
    def __getitem__(self, k):
        if k not in self:
            self[k] = nikkyai.NikkyAI(id=k, context_lines=CONTEXT_LINES)
        return dict.__getitem__(self, k)


class NikkyBotFactory(protocol.ReconnectingClientFactory):

    protocol = nikkybot.NikkyBot

    def __init__(self, opts):

        self.opts = opts
        self.opts.channels = set([nikkybot.irc_lower(c) for c in
                                 self.opts.channels])

        self.servers = [(s.split(':')[0], int(s.split(':')[1])) for s in
                        opts.servers]
        self.shut_down = False
        self.nikkies = DefaultNikkyAIDict()
        self.factor = 1.5
        self.maxDelay = 600

    def cleanup_state(self):
        """Clean up any stale state data to reduce memory and disk usage"""
        for k in self.nikkies:
            print('Starting state cleanup for {}'.format(repr(k)))
            self.nikkies[k].clean_up_last_replies()

    def rebuild(self):
        """Reload NikkyBot module"""
        rebuild(nikkybot)

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed: {}'.format(reason))
        url, port = random.choice(self.servers)
        print('Connecting to {}:{}'.format(url, port))
        self.connector = connector
        connector.host, connector.port = url, port
        self.retry()

    def clientConnectionLost(self, connector, reason):
        if self.shut_down:
            reactor.stop()
        else:
            self.clientConnectionFailed(connector, reason)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-s', '--servers', nargs='*', metavar='SERVER',
                    default=['irc.choopa.net:6667',
                             'efnet.port80.se:6667',
                             'efnet.portlane.se:6667',
                    ],
                    help='List of servers to connect to (host:port)')
    ap.add_argument('--real-name', default='NikkyBot',
                    help='"Real name" to provide to IRC server')
    ap.add_argument('-n', '--nicks', nargs='*', metavar='NICK',
                    default=['nikkybot', 'nikkybot2', 'nikkybot_'],
                    help='List of nicks to use, in descending order of '
                         'preference')
    ap.add_argument('-c', '--channels', nargs='*', metavar='CHANNEL',
                    default=[], help='List of channels to join')
    ap.add_argument('--client-version',
                    default="NikkyBot (Twisted IRC bot)--contact: 'tev' or "
                            "travisgevans@gmail.com",
                    help='Client version response to give to CTCP VERSION '
                         'requests')
    ap.add_argument('--admin-hostmasks', nargs='*', metavar='ADMIN_HOSTMASK',
                    default=['*!admin@example.com',],
                    help='Trusted hostmasks to accept special admin commands '
                         'from')
    ap.add_argument('--max-line-length', default=256, type=int,
                    help='Maximum characters to send per line in messages')
    ap.add_argument('--min-send-time', default=1, type=float,
                    help='Minimum allowed time in seconds between message '
                         'lines sent')
    ap.add_argument('--nick-retry-wait', default=300, type=float,
                    help='Seconds to wait before trying to reclain preferred '
                         'nick')
    ap.add_argument('--initial-reply-delay', default=1, type=float,
                    help='Seconds to wait before first line sent')
    ap.add_argument('--simulated-typing-speed', default=.1, type=float,
                    help='Seconds per character to delay message (simulated '
                         'typing delay)')
    ap.add_argument('--direct-response-time', default=4, type=float,
                    help='Seconds to search for responses to highlight '
                         'messages')
    ap.add_argument('--random-response-time', default=10, type=float,
                    help='Seconds to search for responses to non-highlight '
                         'messages')
    ap.add_argument('--state-cleanup-interval', default=60*60*24, type=float,
                    help='Seconds to do AI state housekeeping/cleanup')
    ap.add_argument('--channel-check-interval', default=300, type=float,
                    help='Seconds to check joined channels and rejoin if '
                         'necessary')
    ap.add_argument('--max-user-threads', default=4, type=int,
                    help='Maximum threads invoked from untrusted commands to '
                         'run simultaneously')
    ap.add_argument('--flood-protect', nargs=3, default=None,
                    metavar=('INTERVAL', 'MAX-MSGS', 'COOLDOWN'), type=int,
                    help='Enable flood protection, accepting no more than MAX-MSGS '
                         'messages at a time per user during INTERVAL seconds.  If '
                         'this is exceeded, ignore that user until they cease '
                         'sending messages for COOLDOWN seconds.')
    OPTS = ap.parse_args()

    log.startLogging(sys.stdout)
    url, port = random.choice(OPTS.servers).split(':')
    print('Connecting to {}:{}'.format(url, port))
    reactor.connectTCP(url, int(port), NikkyBotFactory(OPTS))
    reactor.run()

