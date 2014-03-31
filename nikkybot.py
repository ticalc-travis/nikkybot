#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# “NikkyBot”
# Copyright ©2012 Travis Evans
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

import argparse
import cPickle
import random
import re
import subprocess
import time
import traceback
import sys
import psycopg2

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, threads
from twisted.internet.error import ConnectionDone
from twisted.python import log

from nikkyai import NikkyAI
import markovmixai

OPTS = argparse.Namespace()

class BotError(Exception):
    pass


class UnrecognizedCommandError(BotError):
    pass


class NikkyBot(irc.IRCClient):

    ## Overridden methods ##

    def join(self, channel):
        """Log bot's channel joins"""
        print('Joining {}'.format(channel))
        irc.IRCClient.join(self, channel)

    def leave(self, channel, reason):
        """Log bot's channel parts"""
        print('Leaving {}: {}'.format(channel, reason))
        irc.IRCClient.leave(self, channel, reason)

    def msg(self, target, message, length=None):
        """Provide default line length before split"""
        if length is None:
            length = OPTS.max_line_length
        irc.IRCClient.msg(self, target, message, length)

    def nickChanged(self, nick):
        """Update NikkyAIs with new nick"""
        irc.IRCClient.nickChanged(self, nick)
        for n in self.nikkies.values():
            n.nick = self.nickname

    def alterCollidedNick(self, nickname):
        """Resolve nick conflicts and set up automatic preferred nick
        reclaim task"""
        reactor.callLater(self.factory.nick_retry_wait, self.reclaim_nick)
        try:
            return self.factory.nicks[self.factory.nicks.index(nickname) + 1]
        except IndexError:
            return self.factory.nicks[0] + '_'

    ## Callbacks ##

    def connectionMade(self):
        print('Connection established.')
        self.factory.resetDelay()
        self.factory.shut_down = False
        self.nickname = self.factory.nicks[0]
        self.versionName = self.factory.client_version
        self.realname = self.factory.real_name
        self.lineRate = self.factory.min_send_time
        self.nikkies = self.factory.nikkies
        self.pending_responses = []
        self.joined_channels = set()
        self.user_threads = 0

        irc.IRCClient.connectionMade(self)

        if OPTS.reload_interval:
            reactor.callLater(OPTS.reload_interval, self.auto_reload)
        if OPTS.channel_check_interval:
            reactor.callLater(OPTS.channel_check_interval, self.channel_check)
        if OPTS.state_save_interval and OPTS.state_file:
            reactor.callLater(OPTS.state_save_interval, self.save_state)
        if OPTS.state_cleanup_interval:
            reactor.callLater(OPTS.state_cleanup_interval, self.cleanup_state)

    def connectionLost(self, reason):
        print('Connection lost: {}'.format(reason))
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        for channel in self.factory.channels:
            self.join(channel)
            self.nikkies[channel].nick = self.nickname

    def joined(self, channel):
        self.joined_channels.add(channel)

    def privmsg(self, user, channel, msg):
        nick, host = user.split('!', 1)

        formatted_msg = '<{}> {}'.format(nick, msg)

        # !TODO! Clean up this mess. This is getting ridiculous.

        if channel == self.nickname:
            # Private message
            if self.any_hostmask_match(self.factory.admin_hostmasks, user):
                try:
                    self.do_command(msg.strip(), nick)
                except UnrecognizedCommandError:
                    try:
                        self.do_guest_command(msg.strip(), nick)
                    except UnrecognizedCommandError:
                        self.do_AI_reply(formatted_msg, nick, no_delay=True,
                                         log_response=False)
                    else:
                        print('Executed: {}'.format(msg.strip()))
                else:
                    print('Executed: {}'.format(msg.strip()))
            else:
                print('privmsg from {}: {}'.format(user, repr(msg)))
                try:
                    self.do_guest_command(msg.strip(), nick)
                except UnrecognizedCommandError:
                    self.do_AI_reply(formatted_msg, nick, no_delay=True)
                else:
                    print('Executed: {}'.format(msg.strip()))
        else:
            # Public message
            if self.hostmask_match('*!~saxjax@*', user):
                m = re.match(r'\(.\) \[(.*)\] (.*)', msg)
                if m:
                    nick = m.group(1)
                    formatted_msg = '<{}> {}'.format(nick, m.group(2))
                else:
                    m = re.match(r'\(.\) \*(.*?) (.*)', msg)
                    if m:
                        if m.group(1) != 'File':
                            nick = m.group(1)
                        else:
                            nick = ''
                        formatted_msg = '<> {} {}'.format(m.group(1),
                                                          m.group(2))
            if self.is_highlight(msg):
                raw_msg = msg
                for n in self.factory.nicks:
                    m = re.match(r'^{}[:,]? (.*)'.format(re.escape(n)),
                                 msg, flags=re.I)
                    if m:
                        raw_msg = m.group(1).strip()
                        try:
                            self.do_guest_command(raw_msg, nick,
                                                  channel=channel)
                        except UnrecognizedCommandError:
                            self.do_AI_reply(formatted_msg, channel,
                                             log_response=False)
                        else:
                            print('Executed: {}'.format(raw_msg.strip()))
                        break
                else:
                    self.do_AI_reply(formatted_msg, channel,
                                     log_response=False)
            else:
                self.do_AI_maybe_reply(formatted_msg, channel, log_response=False)

    def action(self, user, channel, msg):
        """Pass actions to AI like normal lines"""
        self.privmsg(user, channel, msg)

    def ctcpQuery(self, user, channel, messages):
        """Just log private CTCPs for the heck of it"""
        for tag, data in messages:
            if channel == self.nickname:
                print('private CTCP {} from {}: {}'.format(tag, user, data))
        irc.IRCClient.ctcpQuery(self, user, channel, messages)

    def noticed(self, user, channel, message):
        """Log private notices, too, but don't do anything else with them"""
        if channel == self.nickname:
            print('private NOTICE from {}: {}'.format(user, message))

    def kickedFrom(self, channel, kicker, message):
        """On kick, automatically try to rejoin after a bit"""
        reactor.callLater(random.randint(5, 300), self.join, channel)

    def irc_unknown(self, prefix, command, parms):
        if command == "INVITE" and parms[1] in CHANNELS:
            self.join(parms[1])
            print('Received invite to {}; trying to join'.format(parms[1]))
        elif command == "PONG":
            pass
        else:
            print('unknown: {0}, {1}, {2}'.format(prefix, command, parms))

    ## Custom methods ##

    def reclaim_nick(self):
        """Attempt to reclaim preferred nick (self.alterCollidedNick will
        set up this function to be called again later on failure)"""
        if self.nickname != self.factory.nicks[0]:
            self.setNick(self.factory.nicks[0])

    def hostmask_match(self, testmask, knownmask):
        """Check if knownmask matches against testmask, resovling wildcards
        in testmask"""
        testmask = \
            testmask.replace('.', '\\.').replace('?', '.').replace('*', '.*')
        return re.match(testmask, knownmask)

    def any_hostmask_match(self, testmasks, knownmask):
        """Check if knownmask matches against any of the masks in iterable
        testmasks, resolving wildcards in testmasks"""
        for mask in testmasks:
            if self.hostmask_match(mask, knownmask):
                return True
        return False

    def is_highlight(self, msg):
        """Check if msg contains an instance of one of bot's nicknames"""
        for nick in self.factory.nicks:
            if re.search(r'\b{}\b'.format(re.escape(nick)),
                         msg, flags=re.I):
                return True
        return False

    def report_error(self, source, silent=False):
        """Log a traceback if NikkyAI fails due to an unhandled exception
        while generating a response, and respond with a random amusing line
        if silent is False"""
        if not silent:
            pub_reply = random.choice(['Oops', 'Ow, my head hurts', 'TEV YOU SCREWED YOUR CODE UP AGAIN', 'Sorry, lost my marbles for a second', 'I forgot what I was going to say', 'Crap, unhandled exception again', 'TEV: FIX YOUR CODE PLZKTHX', 'ERROR: Operation failed successfully!', "Sorry, I find you too lame to give you a proper response", "Houston, we've had a problem.", 'Segmentation fault', 'This program has performed an illegal operation and will be prosecuted^H^H^H^H^H^H^H^H^H^Hterminated.', 'General protection fault', 'Guru Meditation #00000001.1337... wait, wtf? What kind of system am I running on, anyway?', 'Nikky panic - not syncing: TEV SUCKS', 'This is a useless error message. An error occurred. Goodbye.', 'HCF', 'ERROR! ERROR!', '\001ACTION explodes due to an error\001'])
        print('\n=== Exception ===\n\n')
        traceback.print_exc()
        print()

    def do_command(self, cmd, nick):
        """Execute a special/admin command"""
        if cmd.lower().startswith('?quit'):
            try:
                msg = cmd.split(' ', 1)[1]
            except IndexError:
                msg = 'Shutdown initiated'
            self.quit(msg)
            self.factory.shut_down = True
        elif cmd.lower().startswith('?reload'):
            try:
                self.reload_ai()
            except Exception as e:
                print('\n=== Exception ===\n\n')
                traceback.print_exc()
                print()
                self.notice(nick, 'Reload error: {}'.format(e))
            else:
                self.notice(nick, 'Reloaded nikkyai')

        elif cmd.lower().startswith('?code '):
            try:
                exec(cmd.split(' ', 1))[1]
            except Exception as e:
                print('\n=== Exception ===\n\n')
                traceback.print_exc()
                print()
                self.notice(nick, 'Error: {}'.format(e))
        else:
            raise UnrecognizedCommandError

    def return_bot_chat(self, t):
        nick, channel, output = t
        if channel is not None:
            self.output_timed_msg(channel,
                                  '{}: Botchat result: {}'.format(nick, output))
        else:
            self.output_timed_msg(nick, 'Botchat result: {}'.format(output))
        print('return_bot_chat: Reporting botchat completion: {}'.format(output))
        self.user_threads -= 1
        assert(self.user_threads >= 0)

    def exec_bot_chat(self, nick, channel, nick1, nick2):
        self.user_threads += 1
        out = subprocess.check_output(['./bot-chat', nick1, nick2])
        assert(out.count('\n') <= 2)
        return nick, channel, out

    def bot_chat_error(self, failure, nick):
        reactor.callLater(2, self.notice, nick,
                          'Sorry, something went wrong. Tell tev!')
        self.user_threads -= 1
        assert(self.user_threads >= 0)
        return failure

    def do_guest_command(self, cmd, nick, channel=None):
        """Execute a special/non-admin command"""
        if cmd.lower().startswith('?botchat'):
            reload(sys.modules['markovmixai'])
            personalities = markovmixai.get_personalities()
            usage_msg1 = 'Usage: ?botchat personality1 personality2'
            usage_msg2 = 'Personalities: {}'.format(
                            ', '.join(sorted(personalities)))
            parms = cmd.split(' ')[1:]  #Excluding '?botchat' itself
            if (len(parms) != 2 or parms[0] not in personalities or
                    parms[1] not in personalities):
                reactor.callLater(2, self.notice, nick, usage_msg1)
                reactor.callLater(4, self.notice, nick, usage_msg2)
            else:
                if self.user_threads >= MAX_USER_THREADS:
                    reactor.callLater(2, self.notice, nick,
                                      "Sorry, I'm too busy at the moment. Please try again later!")
                else:
                    reactor.callLater(2, self.notice, nick,
                                    "Generating the bot chat may take a while... I'll let you know when it's done!")
                    d = threads.deferToThread(self.exec_bot_chat, nick, channel,
                                            parms[0], parms[1])
                    d.addErrback(self.bot_chat_error, nick)
                    d.addCallback(self.return_bot_chat)
        else:
            raise UnrecognizedCommandError

    def do_AI_reply(self, msg, target, silent_errors=False, log_response=True,
            no_delay=False):
        """Output an AI response for the given msg to target (user or channel)
        trapping for exceptions"""
        try:
            reply = self.nikkies[target].reply(msg)
        except psycopg2.OperationalError:
            """Try to reconnect to DB backend and try again"""
            print('WARNING: DB backend error; reloading and trying again')
            time.sleep(5)
            self.reload_ai()
            time.sleep(5)
            self.do_AI_reply(msg, target, silent_errors, log_response,
                             no_delay)
        except Exception:
            self.report_error(target, silent_errors)
        else:
            if reply and log_response:
                print('privmsg to {}: {}'.format(target, repr(reply)))
            if reply:
                self.output_timed_msg(target, reply, no_delay=no_delay)

    def do_AI_maybe_reply(self, msg, target, silent_errors=True,
            log_response=False):
        """Occasionally reply to the msg given, or say a random remark"""
        try:
            reply = self.nikkies[target].decide_remark(msg)
        except Exception:
            self.report_error(target, silent_errors)
        else:
            if reply and log_response:
                print('privmsg response to {}: {}'.format(target, repr(reply)))
            if reply:
                self.output_timed_msg(target, reply)

    def output_timed_msg(self, target, msg, no_delay=False):
        """Output msg paced at a simulated typing rate.  msg will be split
        into separate lines if it contains \n characters."""

        if no_delay:
            delay = 2
            rate = 0
        else:
            delay = self.factory.initial_reply_delay
            rate = self.factory.simulated_typing_speed

        if isinstance(msg, str) or isinstance(msg, unicode):
            msg = [msg]
        for item in msg:
            for line in item.split('\n'):
                if line:
                    self.pending_responses.append(
                        (delay + len(line)*rate, target, line)
                    )
        self.schedule_next_msg()

    def schedule_next_msg(self, _lastTime=0):
        """Kick off timed event for next queued line to be output"""
        try:
            time, target, msg = self.pending_responses.pop(0)
        except IndexError:
            pass
        else:
            reactor.callLater(_lastTime + time, self.msg, target,
                            self.escape_message(msg), length=256)
            reactor.callLater(_lastTime + time + 1, self.schedule_next_msg)

    def escape_message(self, msg):
        """'Escape' a message by inserting an invisible control character
        at the beginning in some cases, to avoid trigger public bot
        commands."""
        if msg[0] in '~!?@#$%^&*-.,;:' and not msg.startswith('!qfind'):
            return '\x0F' + msg
        else:
            return msg

    def reload_ai(self):
        reload(sys.modules['nikkyai'])
        from nikkyai import NikkyAI
        for k in self.nikkies:
            last_replies = self.nikkies[k].last_replies
            self.nikkies[k] = NikkyAI()
            self.nikkies[k].last_replies = last_replies
            self.nikkies[k].nick = self.nickname
            self.nikkies[k].load_preferred_keywords()

    def auto_reload(self):
        """Automatically reload AI module on intervals (to update regularly
        updated Markov data by another process, for instance)"""
        self.reload_ai()
        reactor.callLater(OPTS.reload_interval, self.auto_reload)

    def channel_check(self):
        """Retry any channels that we apparently didn't successfully join for
        some reason."""
        for c in self.factory.channels:
            if c not in self.joined_channels:
                self.join(c)

    def save_state(self):
        """Save nikkyAI state to disk file"""
        self.factory.save_state()
        reactor.callLater(OPTS.state_save_interval, self.save_state)

    def cleanup_state(self):
        """Clean up any stale state data to reduce memory and disk usage"""
        self.factory.cleanup_state()
        reactor.callLater(OPTS.state_cleanup_interval, self.cleanup_state)


class NikkyBotFactory(protocol.ReconnectingClientFactory):

    protocol = NikkyBot

    def __init__(self, OPTS):

        self.servers = [(s.split(':')[0], int(s.split(':')[1])) for s in
                        OPTS.servers]
        self.channels = OPTS.channels
        self.nicks = OPTS.nicks
        self.real_name = OPTS.real_name
        self.admin_hostmasks = OPTS.admin_hostmasks
        self.client_version = OPTS.client_version
        self.initial_reply_delay = OPTS.initial_reply_delay
        self.reconnect_wait = OPTS.reconnect_wait
        self.min_send_time = OPTS.min_send_time
        self.nick_retry_wait = OPTS.nick_retry_wait
        self.simulated_typing_speed = OPTS.simulated_typing_speed
        self.state_file = OPTS.state_file

        self.shut_down = False

        self.nikkies = defaultdict(NikkyAI)
        self.load_state()

    def load_state(self):
        """Attempt to load persistent state data; else start with new
        defaults"""
        if not self.state_file:
            return
        try:
            f = open(self.state_file, 'rb')
        except IOError as e:
            print("Couldn't open state data file for reading: {}".format(e))
        else:
            try:
                state = cPickle.load(f)
            except Exception as e:
                print("Couldn't load state data: {}".format(e))
            else:
                for k in state:
                    try:
                        nikky = self.nikkies[k]
                    except KeyError:
                        pass
                    else:
                        nikky.last_replies = state[k]['last_replies']
                        try:
                            nikky.load_preferred_keywords()
                        except Exception as e:
                            print("Couldn't load preferred keyword patterns: {}".format(e))
                print("Loaded state data")

    def save_state(self):
        """Save persistent state data"""
        if not self.state_file:
            return
        try:
            f = open(self.state_file, 'wb')
        except IOError as e:
            print(
                "Couldn't open state data file for writing: {}".format(e))
        else:
            state = {}
            for k in self.nikkies:
                state[k] = {'last_replies': self.nikkies[k].last_replies}
            try:
                cPickle.dump(state, f)
            except Exception as e:
                print("Couldn't save state data: {}".format(e))
            else:
                print("Saved state data")

    def cleanup_state(self):
        """Clean up any stale state data to reduce memory and disk usage"""
        for k in self.nikkies:
            print('Starting state cleanup for {}'.format(repr(k)))
            self.nikkies[k].clean_up_last_replies()

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed: {}'.format(reason))
        url, port = random.choice(self.servers)
        print('Waiting {} seconds'.format(self.reconnect_wait))
        time.sleep(self.reconnect_wait)
        print('Connecting to {}:{}'.format(url, port))
        reactor.connectTCP(url, port,
            NikkyBotFactory(OPTS))

    def clientConnectionLost(self, connector, reason):
        self.save_state()
        if self.shut_down:
            reactor.stop()
        else:
            self.clientConnectionFailed(connector, reason)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-s', '--servers', nargs='*', metavar='SERVER',
                    default=['irc.choopa.net:6667', 'efnet.port80.se:6667',
                             'irc.eversible.net:6667', 'irc.shoutcast.com:6667',
                             'irc.teksavvy.ca:6667', 'irc.paraphysics.net:6667'],
                    help='List of servers to connect to (host:port)')
    ap.add_argument('--real-name', default='NikkyBot',
                    help='"Real name" to provide to IRC server')
    ap.add_argument('-n', '--nicks', nargs='*', metavar='NICK',
                    default=['nikkybot', 'nikkybot2', 'nikkybot_'],
                    help='List of nicks to use, in descending order of '
                         'preference')
    ap.add_argument('-c', '--channels', nargs='*', metavar='CHANNEL',
                    default=['#flood', '#markov', '#cemetech'],
                    help='List of channels to join')
    ap.add_argument('--client-version',
                    default="nikkybot (twisted IRC bot)--contact 'tev' or "
                            "travisgevans@gmail.com",
                    help='Client version response to give to CTCP VERSION '
                         'requests')
    ap.add_argument('--admin-hostmasks', nargs='*', metavar='ADMIN_HOSTMASK',
                    default=['*!ijel@ip68-102-86-156.ks.ok.cox.net',
                             '*!travise@nvm2u.com', '*!travise@64.13.172.47'],
                    help='Trusted hostmasks to accept special admin commands '
                         'from')
    ap.add_argument('--reconnect-wait', default=30, type=float,
                    help='Seconds to wait before trying to reconnect on '
                         'connection failure')
    ap.add_argument('--max-line-length', default=256, type=int,
                    help='Maximum characters to send per line in messages')
    ap.add_argument('--min-send-time', default=1, type=float,
                    help='Minimum allowed time in seconds between message '
                         'lines sent')
    ap.add_argument('--nick-retry-wait', default=300, type=float,
                    help='Seconds to wait before trying to reclain preferred '
                         'nick')
    ap.add_argument('--initial-reply-delay', default=2, type=float,
                    help='Seconds to wait before first line sent')
    ap.add_argument('--simulated-typing-speed', default=.1, type=float,
                    help='Seconds per character to delay message (simulated '
                         'typing delay)')
    ap.add_argument('-t', '--state-file', default=None,
                    help='Path for AI save-state file (no permanent state '
                         'data saved if not given)')
    ap.add_argument('--reload-interval', default=60*60*24, type=float,
                    help='Seconds to automatically reload NikkyAI module')
    ap.add_argument('--state-save-interval', default=900, type=float,
                    help='Seconds to save AI state')
    ap.add_argument('--state-cleanup-interval', default=60*60*24, type=float,
                    help='Seconds to do AI state housekeeping/cleanup')
    ap.add_argument('--channel-check-interval', default=300, type=float,
                    help='Seconds to check joined channels and rejoin if '
                         'necessary')
    ap.add_argument('--max-user-threads', default=4, type=int,
                    help='Maximum threads invoked from untrusted commands to '
                         'run simultaneously')
    OPTS = ap.parse_args()

    log.startLogging(sys.stdout)
    url, port = random.choice(OPTS.servers).split(':')
    print('Connecting to {}:{}'.format(url, port))
    reactor.connectTCP(url, int(port), NikkyBotFactory(OPTS))
    reactor.run()

