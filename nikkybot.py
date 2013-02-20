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

import random
import re
import time
import traceback
import sys

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.internet.error import ConnectionDone
from twisted.python import log

from config import *
from nikkyai import NikkyAI


RELOAD_INTERVAL = 60 * 60 * 24


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
        
    def msg(self, target, message, length=MAX_LINE_LENGTH):
        """Provide default line length before split"""
        irc.IRCClient.msg(self, target, message, length)
        
    def nickChanged(self, nick):
        """Update NikkyAIs with new nick"""
        irc.IRCClient.nickChanged(self, nick)
        for n in self.nikkies.values():
            n.nick = self.nickname
        
    def alterCollidedNick(self, nickname):
        """Resolve nick conflicts and set up automatic preferred nick
        reclaim task"""
        try:
            return self.factory.nicks[self.factory.nicks.index(nickname) + 1]
        except IndexError:
            return self.factory.nicks[0] + '_'
        reactor.callLater(self.nick_retry_wait, self.reclaim_nick)

    ## Callbacks ##

    def connectionMade(self):
        print('Connection established.')
        self.factory.resetDelay()
        self.factory.shut_down = False
        self.nickname = self.factory.nicks[0]
        self.lineRate = self.factory.min_send_time
        self.versionName = self.factory.client_version
        self.nikkies = self.factory.nikkies
        self.pending_responses = []

        irc.IRCClient.connectionMade(self)

        if RELOAD_INTERVAL is not None:
            reactor.callLater(RELOAD_INTERVAL, self.auto_reload)

    def connectionLost(self, reason):
        print('Connection lost: {}'.format(reason))
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        for channel in self.factory.channels:
            self.join(channel)
            self.nikkies[channel].nick = self.nickname

    def privmsg(self, user, channel, msg):
        nick, host = user.split('!', 1)
        formatted_msg = '<{}> {}'.format(nick, msg)

        if channel == self.nickname:
            # Private message
            if self.any_hostmask_match(self.factory.admin_hostmasks, user):
                try:
                    self.do_command(msg.strip(), nick)
                except UnrecognizedCommandError:
                    self.do_AI_reply(formatted_msg, nick, no_delay=True,
                        log_response=False)
                else:
                    print('Executed: {}'.format(msg.strip()))
            else:
                print('privmsg from {}: {}'.format(user, repr(msg)))
                self.do_AI_reply(formatted_msg, nick, no_delay=True)
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
                        nick = m.group(1)
                        formatted_msg = '<{}> {}'.format(nick, m.group(2))
            if self.is_highlight(msg):
                self.do_AI_reply(formatted_msg, channel, log_response=False)
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
            if re.search(r'\b{}\b'.format(re.escape(self.nickname)),
                         msg, flags=re.I):
                return True
        return False
            
    def report_error(self, source, silent=False):
        """Log a traceback if NikkyAI fails due to an unhandled exception 
        while generating a response, and respond with a random amusing line
        if silent is False"""
        if not silent:
            pub_reply = random.choice(['Oops', 'Ow, my head hurts', 'TEV YOU SCREWED YOUR CODE UP AGAIN', 'Sorry, lost my marbles for a second', 'I forgot what I was going to say', 'Crap, unhandled exception again', 'TEV: FIX YOUR CODE PLZKTHX', 'ERROR: Operation failed successfully!', "Sorry, I find you too lame to give you a proper response", "Houston, we've had a problem.", 'Segmentation fault', 'This program has performed an illegal operation and will be prosecuted^H^H^H^H^H^H^H^H^H^Hterminated.', 'General protection fault', 'Guru Meditation #00000001.1337... wait, wtf? What kind of system am I running on, anyway?', 'Nikky panic - not syncing: TEV SUCKS', 'This is a useless error message. An error occurred. Goodbye.', 'HCF', 'ERROR! ERROR!', '\001ACTION explodes due to an error\001'])
            self.msg(source, pub_reply)
        print('\n=== Exception ===\n\n')
        traceback.print_exc()
        print()
        
    def do_command(self, cmd, nick):
        """Execute a special/admin command"""
        if cmd.startswith('?quit'):
            try:
                msg = cmd.split(' ', 1)[1]
            except IndexError:
                msg = 'Shutdown initiated'
            self.quit(msg)
            self.factory.shut_down = True
        elif cmd.startswith('?reload'):
            try:
                self.reload_ai()
            except Exception as e:
                print('\n=== Exception ===\n\n')
                traceback.print_exc()
                print()
                self.notice(nick, 'Reload error: {}'.format(e))
            else:
                self.notice(nick, 'Reloaded nikkyai')

        elif cmd.startswith('?code '):
            try:
                exec(cmd.split(' ', 1))[1]
            except Exception as e:
                print('\n=== Exception ===\n\n')
                traceback.print_exc()
                print()
                self.notice(nick, 'Error: {}'.format(e))
        else:
            raise UnrecognizedCommandError
    
    def do_AI_reply(self, msg, target, silent_errors=False, log_response=True,
            no_delay=False):
        """Output an AI response for the given msg to target (user or channel)
        trapping for exceptions"""
        try:
            reply = self.nikkies[target].reply(msg)
        except:
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
        except:
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
        if (msg[0] in '~!?@#$%^&*-.,;:'
            and not msg.startswith('!k ')
            and not msg.startswith('!q ')
            and not msg.startswith('!qfind ')
            and not msg.startswith('!qsay ')
            and not msg.startswith('!seen ')):
        # Change the above line to the following one once the fun's over
        #if msg[0] in '~!?@#$%^&*-.,;:':
            print('Escaping/"protecting" message: {}'.format(msg))
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

    def auto_reload(self):
        """Automatically reload AI module on intervals (to update regularly-updated
        Markov data by another process, for instance)"""
        self.reload_ai()
        reactor.callLater(RELOAD_INTERVAL, self.auto_reload)


class NikkyBotFactory(protocol.ReconnectingClientFactory):
    
    protocol = NikkyBot

    def __init__(self, servers, channels, nicks, real_name=REAL_NAME,
                 admin_hostmasks=ADMIN_HOSTMASKS,
                 client_version=CLIENT_VERSION,
                 min_send_time=MIN_SEND_TIME,
                 nick_retry_wait=NICK_RETRY_WAIT,
                 initial_reply_delay=INITIAL_REPLY_DELAY,
                 simulated_typing_speed=SIMULATED_TYPING_SPEED):
        self.servers = servers
        self.channels = channels
        self.nicks = nicks
        self.real_name = real_name
        self.admin_hostmasks = admin_hostmasks
        self.client_version = client_version
        self.initial_reply_delay = initial_reply_delay
        self.min_send_time = min_send_time
        self.nick_retry_wait = nick_retry_wait
        self.simulated_typing_speed = simulated_typing_speed
        
        self.shut_down = False
        
        self.nikkies = defaultdict(NikkyAI)

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed: {}'.format(reason))
        url, port = random.choice(self.servers)
        print('Connecting to {}:{}'.format(url, port))
        reactor.connectTCP(url, port,
            NikkyBotFactory(self.servers, self.channels, self.nicks,
                self.real_name, self.admin_hostmasks, self.min_send_time,
                self.nick_retry_wait, self.simulated_typing_speed))
                
    def clientConnectionLost(self, connector, reason):
        if self.shut_down:
            reactor.stop()
        else:
            protocol.ReconnectingClientFactory.clientConnectionLost(
                self, connector, reason)


if __name__ == '__main__':
    log.startLogging(sys.stdout)
    url, port = random.choice(SERVERS)
    print('Connecting to {}:{}'.format(url, port))
    reactor.connectTCP(url, port, NikkyBotFactory(SERVERS, CHANNELS, NICKS))
    reactor.run()
    
