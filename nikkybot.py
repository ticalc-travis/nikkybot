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

import random
import re
import subprocess
from time import time as now
import traceback
import sys
import psycopg2

from twisted.python.rebuild import Sensitive, rebuild
from twisted.words.protocols import irc
from twisted.internet import reactor, threads

from nikkyai import NikkyAI
import personalitiesrc


class BotError(Exception):
    pass


class UnrecognizedCommandError(BotError):
    pass


class UnauthorizedCommandError(BotError):
    pass


class NikkyBot(irc.IRCClient, Sensitive):

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
            length = self.opts.max_line_length
        irc.IRCClient.msg(self, target, message, length)

    def nickChanged(self, nick):
        """Update NikkyAIs with new nick"""
        irc.IRCClient.nickChanged(self, nick)

    def alterCollidedNick(self, nickname):
        """Resolve nick conflicts and set up automatic preferred nick
        reclaim task"""
        reactor.callLater(self.opts.nick_retry_wait, self.reclaim_nick)
        try:
            return self.opts.nicks[self.opts.nicks.index(nickname) + 1]
        except IndexError:
            return self.opts.nicks[0] + '_'

    ## Callbacks ##

    def connectionMade(self):
        print('Connection established.')
        self.factory.resetDelay()
        self.factory.shut_down = False
        self.opts = self.factory.opts
        self.nickname = self.opts.nicks[0]
        self.nikkies = self.factory.nikkies
        self.pending_responses = []
        self.joined_channels = set()
        self.user_threads = 0
        self.pending_msg_time = now()

        irc.IRCClient.connectionMade(self)

        if self.opts.channel_check_interval:
            reactor.callLater(self.opts.channel_check_interval, self.channel_check)
        if self.opts.state_cleanup_interval:
            reactor.callLater(self.opts.state_cleanup_interval, self.cleanup_state)

    def connectionLost(self, reason):
        print('Connection lost: {}'.format(reason))
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        for channel in self.opts.channels:
            self.join(channel)

    def joined(self, channel):
        self.joined_channels.add(channel)

    def privmsg(self, user, target, msg):
        nick, host = user.split('!', 1)
        formatted_msg = '<{}> {}'.format(nick, msg)
        msg = msg.strip()
        is_private = target == self.nickname
        sender = nick if is_private else target
        is_admin = self.any_hostmask_match(self.opts.admin_hostmasks, user)
        is_highlight = self.is_highlight(msg)

        # Strip any nick highlight from beginning of line
        m = re.match(r'^{}[:,]? (.*)'.format(re.escape(self.nickname)),
                    msg, flags=re.I)
        has_leading_highlight = False
        if m:
            has_leading_highlight = True
            msg = m.group(1).strip()

        # Log private messages
        if is_private:
            print('privmsg from {} {}: {}'.format(
                user, '[ADMIN]' if is_admin else '', msg))

        # Parse/convert saxjax's messages
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
                    formatted_msg = '<> {} {}'.format(m.group(1), m.group(2))

        # Determine what to do (reply, maybe reply, run command)
        if is_private or is_highlight:
            if is_private or has_leading_highlight:
                try:
                    self.do_command(msg, nick, target, is_admin)
                    print('Executed: {}'.format(msg))
                except (UnrecognizedCommandError, UnauthorizedCommandError):
                    self.do_AI_reply(formatted_msg, sender,
                                     no_delay=is_private, log_response=is_private)
            else:
                self.do_AI_reply(formatted_msg, sender, no_delay=is_private,
                                 log_response=is_private)
        else:
            self.do_AI_maybe_reply(formatted_msg, sender, log_response=False)

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
        if command == "INVITE":
            if parms[1] in CHANNELS:
                self.join(parms[1])
                print('Received invite to {}; trying to join'.format(parms[1]))
            else:
                print('Ignoring invite to unrecognized channel '
                      '{}'.format(parms[1]))
        elif command == "PONG":
            pass
        else:
            print('unknown: {0}, {1}, {2}'.format(prefix, command, parms))

    ## Custom methods ##

    def reclaim_nick(self):
        """Attempt to reclaim preferred nick (self.alterCollidedNick will
        set up this function to be called again later on failure)"""
        if self.nickname != self.opts.nicks[0]:
            self.setNick(self.opts.nicks[0])

    def hostmask_match(self, testmask, knownmask):
        """Check if knownmask matches against testmask, resolving wildcards
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
        """Check if msg contains an instance of bot's current nickname"""
        if re.search(r'\b{}\b'.format(re.escape(self.nickname)),
                     msg, flags=re.I):
            return True
        return False

    def report_error(self, source, silent=False):
        """Log a traceback if NikkyAI fails due to an unhandled exception
        while generating a response, and respond with a random amusing line
        if silent is False"""
        if not silent:
            pub_reply = random.choice(
                ['Oops',
                 'Ow, my head hurts',
                 'TEV YOU SCREWED YOUR CODE UP AGAIN',
                 'Sorry, lost my marbles for a second',
                 'I forgot what I was going to say',
                 'Crap, unhandled exception again',
                 'TEV: FIX YOUR CODE PLZKTHX',
                 'ERROR: Operation failed successfully!',
                 "Sorry, I find you too lame to give you a proper response",
                 "Houston, we've had a problem.",
                 'Segmentation fault',
                 'This program has performed an illegal operation and will be '
                   'prosecuted^H^H^H^H^H^H^H^H^H^Hterminated.',
                 'General protection fault',
                 'Guru Meditation #00000001.1337... wait, wtf? What kind of '
                   'system am I running on, anyway?',
                 'Nikky panic - not syncing: TEV SUCKS',
                 'This is a useless error message. An error occurred. '
                   'Goodbye.',
                 'HCF',
                 'ERROR! ERROR!',
                 '\001ACTION explodes due to an error\001']
            )
            # ...for even more humiliation if we're in one of DecBot's channels
            if source in ('#cemetech', '#flood'):
                pub_reply = random.choice(['','!qadd ']) + pub_reply
            self.msg(source, pub_reply)
        # Log actual exception/traceback
        print('\n=== Exception ===\n\n')
        traceback.print_exc()
        print()

    def do_command(self, msg, src_nick, target, is_admin):
        """Execute a special command"""
        sender = src_nick if target == self.nickname else target
        try:
            cmd, args = msg.split()[0].lower(), ' '.join(msg.split()[1:])
        except IndexError:
            raise UnrecognizedCommandError

        ## Privileged commands ##

        if cmd == '?quit':
            if not is_admin:
                raise UnauthorizedCommandError
            self.quit(args)
            self.factory.shut_down = True

        elif cmd == '?reload':
            if not is_admin:
                raise UnauthorizedCommandError
            try:
                self.reload_ai()
                self.factory.rebuild()
            except Exception as e:
                print('\n=== Exception ===\n\n')
                traceback.print_exc()
                print()
                self.notice(src_nick, 'Reload error: {}'.format(e))
            else:
                self.notice(src_nick, 'Reloaded nikkyai')

        elif cmd == '?join':
            if not is_admin:
                raise UnauthorizedCommandError
            if not args in self.opts.channels:
                self.opts.channels.append(args)
            self.join(args)
            # Update preferred keywords/munges for new channel
            pk = set()
            ml = set()
            self.nikkies[args]      # Summon new channel NikkyAI into existence
            for nikky in self.nikkies.values():
                pk = pk.union(nikky.preferred_keywords)
                ml = ml.union(nikky.munge_list)
            self.nikkies[args].preferred_keywords = pk
            self.nikkies[args].munge_list = ml

        elif cmd == '?part':
            if not is_admin:
                raise UnauthorizedCommandError
            try:
                self.opts.channels.remove(args)
            except ValueError:
                pass
            self.part(args)

        elif cmd == '?addword':
            if not is_admin:
                raise UnauthorizedCommandError
            for nikky in self.nikkies.values():
                nikky.add_preferred_keyword(args)
                self.notice(sender, '{}: Keyword added; {} total'.format(
                    nikky.id, len(nikky.preferred_keywords)))

        elif cmd in ('?delword', '?remword', '?deleteword', '?removeword'):
            if not is_admin:
                raise UnauthorizedCommandError
            for nikky in self.nikkies.values():
                try:
                    nikky.delete_preferred_keyword(args)
                except KeyError:
                    self.notice(sender, '{}: Keyword not found'.format(
                        nikky.id))
                else:
                    self.notice(sender,
                                '{}: Keyword removed; {} total'.format(
                                    nikky.id, len(nikky.preferred_keywords)))

        elif cmd == '?munge':
            if not is_admin:
                raise UnauthorizedCommandError
            self._cmd_add_munge(args)
            self.notice(sender, 'Munge added: {}'.format(args))

        elif cmd == '?unmunge':
            if not is_admin:
                raise UnauthorizedCommandError
            self._cmd_delete_munge(args)
            self.notice(sender, 'Munge deleted: {}'.format(args))

        elif cmd == '?say':
            if not is_admin:
                raise UnauthorizedCommandError
            target, xxx, msg = args.partition(' ')
            self.msg(target, msg)

        elif cmd == '?code':
            if not is_admin:
                raise UnauthorizedCommandError
            try:
                try:
                    ret = eval(args)
                except SyntaxError:
                    exec(args)
                    self.msg(sender, '[exec OK]')
                else:
                    if ret is not None:
                        sret = str(ret)
                        print('{} {}\n{}'.format(cmd, args, sret))
                        if len(sret) > self.opts.max_line_length:
                            sret = sret[:self.opts.max_line_length-1] + '…'
                        self.msg(sender, sret)
                    else:
                        self.msg(sender, '[eval OK]')
            except Exception as e:
                print('\n=== Exception ===\n\n')
                traceback.print_exc()
                print()
                self.notice(sender, 'Error: {}'.format(e))

        ## Public commands ##

        elif cmd in ('botchat', '?botchat'):
            rebuild(personalitiesrc)
            personalities = personalitiesrc.personality_regexes
            usage_msg = 'Usage: ?botchat personality1 personality2'
            parms = args.split(' ')
            try:
                parms[0] = self.nikkies[None].markov.conv_key(parms[0])
                parms[1] = self.nikkies[None].markov.conv_key(parms[1])
            except IndexError:
                pass
            if (len(parms) != 2 or parms[0] not in personalities or
                    parms[1] not in personalities):
                reactor.callLater(2, self.notice, src_nick, usage_msg)
                reactor.callLater(4, self.give_personalities_list, src_nick)
            else:
                if self.user_threads >= self.opts.max_user_threads:
                    reactor.callLater(
                        2, self.notice, src_nick,
                        "Sorry, I'm too busy at the moment. Please try again "
                        "later!")
                else:
                    reactor.callLater(
                        2, self.notice, src_nick,
                        "Generating the bot chat may take a while... I'll let "
                        "you know when it's done!")
                    d = threads.deferToThread(self.exec_bot_chat, src_nick,
                                              sender, parms[0], parms[1])
                    d.addErrback(self.bot_chat_error, src_nick)
                    d.addCallback(self.return_bot_chat)
        elif cmd in ('?personas', '?personalities', 'personas',
                     'personalities'):
            rebuild(personalitiesrc)
            reactor.callLater(2, self.give_personalities_list, src_nick)
            reactor.callLater(4, self.notice, src_nick,
                              'Say "{}: mimic <personality> <message>" to '
                              '"talk" to that personality.'.format(
                                     self.nickname))
            reactor.callLater(6, self.notice, src_nick,
                              'Talk to tev to request a new personality based '
                              'on someone.')
        elif re.match((r"\b(quit|stop|don.?t|do not)\b.*\b(hilite|hilight|highlite|highlight).*\bme"), msg, re.I):
            self._cmd_add_munge(src_nick)
            msg = "Sorry, {}, I'll stop (tell me 'highlight me' to undo)".format(self.nikkies[None].munge_word(src_nick))
            reactor.callLater(2, self.msg, sender, msg)
        elif re.match((r"\b(hilite|hilight|highlite|highlight) me"), msg,
                      re.I):
            self._cmd_delete_munge(src_nick)
            msg = "Okay, {}!".format(src_nick)
            reactor.callLater(2, self.msg, sender, msg)
        else:
            raise UnrecognizedCommandError

    def _cmd_add_munge(self, nick):
        nothing_done = True
        for n in self.nikkies.values():
            if not nick in n.munge_list:
                n.add_munged_word(nick)
                nothing_done = False
        if nothing_done:
            raise UnrecognizedCommandError

    def _cmd_delete_munge(self, nick):
        nothing_done = True
        for n in self.nikkies.values():
            if nick in n.munge_list:
                n.delete_munged_word(nick)
                nothing_done = False
        if nothing_done:
            raise UnrecognizedCommandError

    def give_personalities_list(self, src_nick):
        """Notice a list of available Markov personalities to src_nick"""
        rebuild(personalitiesrc)
        personalities = personalitiesrc.personality_regexes
        msg = 'Personalities: {}'.format(', '.join(sorted(personalities)))
        self.notice(src_nick, msg)

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
        out = subprocess.check_output(['bot-chat', nick1, nick2])
        print('DEBUG: *** Bot chat output ***\n')
        print(out)
        return nick, channel, out

    def bot_chat_error(self, failure, nick):
        reactor.callLater(2, self.notice, nick,
                          'Sorry, something went wrong. Tell tev!')
        self.user_threads -= 1
        assert(self.user_threads >= 0)
        return failure

    def do_AI_reply(self, msg, target, silent_errors=False, log_response=True,
            no_delay=False):
        """Output an AI response for the given msg to target (user or channel)
        trapping for exceptions"""

        # Make sure it knows its correct nick
        self.nikkies[target].nick = self.nickname

        try:
            reply = self.nikkies[target].reply(msg).split('\n')
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

        # Make sure it knows its correct nick
        self.nikkies[target].nick = self.nickname

        try:
            reply = self.nikkies[target].decide_remark(msg).split('\n')
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
            delay = self.opts.initial_reply_delay
            rate = self.opts.simulated_typing_speed

        if isinstance(msg, str) or isinstance(msg, unicode):
            msg = [msg]
        first_line = True
        for item in msg:
            for line in item.split('\n'):
                if line:
                    # Calc time from last line to output this one
                    if first_line:
                        time = (delay + len(line)*rate)
                    else:
                        time = (self.opts.min_send_time + len(line)*rate)
                    # Add line to output queue
                    self.pending_responses.append((time, target, line))
                    first_line = False
        self.schedule_next_msg()

    def schedule_next_msg(self):
        """Kick off timed event for next queued lines to be output"""
        last_time = max(0, self.pending_msg_time-now())
        while self.pending_responses:
            time, target, msg = self.pending_responses.pop(0)
            reactor.callLater(time + last_time, self.msg, target,
                              self.escape_message(msg),
                              length=self.opts.max_line_length)
            last_time += time
        self.pending_msg_time = now() + last_time

    def escape_message(self, msg):
        """'Escape' a message by inserting an invisible control character
        at the beginning in some cases, to avoid triggering public bot
        commands."""
        if (msg[0] in '~!?@#$%^&*-.,;:' and
                not msg.startswith('!qfind') and
                not msg.startswith('!qadd')):
            return '\x0F' + msg
        else:
            return msg

    def reload_ai(self):
        rebuild(sys.modules['nikkyai'])

    def channel_check(self):
        """Retry any channels that we apparently didn't successfully join for
        some reason."""
        for c in self.opts.channels:
            if c not in self.joined_channels:
                self.join(c)

    def cleanup_state(self):
        """Clean up any stale state data to reduce memory and disk usage"""
        self.factory.cleanup_state()
        reactor.callLater(self.opts.state_cleanup_interval, self.cleanup_state)

