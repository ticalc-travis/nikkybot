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

import datetime
import random
import re
import subprocess
from time import time as now
import traceback
import sys

from twisted.python.rebuild import Sensitive, rebuild
from twisted.words.protocols import irc
from twisted.internet import reactor, threads

import nikkyai
import personalitiesrc


def hostmask_match(testmask, knownmask):
    """Check if knownmask matches against testmask, resolving wildcards
    in testmask"""
    testmask = \
        testmask.replace('.', '\\.').replace('?', '.').replace('*', '.*')
    return re.match(testmask, knownmask)


def any_hostmask_match(testmasks, knownmask):
    """Check if knownmask matches against any of the masks in iterable
    testmasks, resolving wildcards in testmasks"""
    for mask in testmasks:
        if hostmask_match(mask, knownmask):
            return True
    return False


def irc_lower(string):
    """Convert string to IRC's idea of lowercase"""
    string = string.lower()
    symb_lower = {'[': '{', ']': '}', '\\': '|', '~': '^'}
    for up, low in symb_lower.items():
        string = string.replace(up, low)
    return string


def sanitize(s):
    """Remove control characters from string 's'"""
    return re.sub('[\x00-\x1f]', '', s)


def strip_color(s):
    return re.sub(r'(?:\x03[0-9]{1,2}(?:,[0-9]{1,2})?|\x02|\x0b|\x0f|\x1d|\x1f)',
                  '', s)


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
        print('Attempting to join {}'.format(channel))
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

    def alterCollidedNick(self, nickname):
        """Resolve nick conflicts and set up automatic preferred nick
        reclaim task"""
        self.set_nick_reclaim_timer()
        try:
            newnick = self.opts.nicks[self.opts.nicks.index(nickname) + 1]
        except IndexError:
            newnick = self.opts.nicks[0] + '_'
        print("Nick collision for {}; using {}".format(
            repr(nickname), repr(newnick)))
        return newnick

    ## Callbacks ##

    def connectionMade(self):
        print('Connection established.')
        self.factory.resetDelay()
        self.factory.shut_down = False
        self.delayed_calls = []
        self.opts = self.factory.opts
        self.nickname = self.opts.nicks[0]
        self.nikkies = self.factory.nikkies
        self.pending_responses = []
        self.user_message_rate = {}
        self.responses_scheduled = False
        self.joined_channels = set()
        self.user_threads = 0
        self.realname = self.opts.real_name
        self.versionName = self.opts.client_version
        self.pending_nick_reclaim_timer = False
        self.last_lines = {}
        self.lineRate = self.opts.min_send_time

        irc.IRCClient.connectionMade(self)

        if self.opts.channel_check_interval:
            self.call_later(self.opts.channel_check_interval, self.channel_check)
        if self.opts.state_cleanup_interval:
            self.call_later(self.opts.state_cleanup_interval, self.cleanup_state)

    def connectionLost(self, reason):
        print('Connection lost: {}'.format(reason))
        for dc in self.delayed_calls:
            if dc.active():
                dc.cancel()
        self.delayed_calls = []
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        for channel in self.opts.channels:
            self.join(channel)

    def joined(self, channel):
        print('Joined channel {}'.format(channel))
        self.joined_channels.add(irc_lower(channel))

    def privmsg(self, user, target, msg):
        nick, msg = self.preparse_msg(user, msg)
        is_private = target == self.nickname

        # For PMs, sender should always be set to the actual IRC client
        # that sent the message, even if we parse a differnet "virtual"
        # nickname from a bridge bot's output; this is where responses
        # will be sent back
        sender = user.split('!')[0] if is_private else target

        is_admin = any_hostmask_match(self.opts.admin_hostmasks, user)
        is_highlight = self.is_highlight(msg)

        # Log private messages
        if is_private:
            print('privmsg from {} {}: {}'.format(
                user, '[ADMIN]' if is_admin else '', msg))

        # Strip any nick highlight from beginning of line
        m = re.match(r'^{}[:,]? (.*)'.format(re.escape(self.nickname)),
                     msg, flags=re.I)
        has_leading_highlight = False
        if m:
            has_leading_highlight = True
            msg = m.group(1).strip()

        # Format message with nick
        if nick:
            msg_with_nick = '<{}> {}'.format(nick, msg)
        else:
            msg_with_nick = msg

        # Log context
        self.nikkies[irc_lower(sender)].last_lines.append(msg_with_nick)

        # Determine what to do (reply, maybe reply, run command)
        if is_private or is_highlight:

            # Apply flood protection for direct responses
            if not is_admin and self.is_flooding(nick):
                print('Too many messages from {}; ignoring'.format(nick))
                return

            if is_private or has_leading_highlight:
                try:
                    self.do_command(msg, nick, target, is_admin)
                    print('Executed: {}'.format(msg))
                except (UnrecognizedCommandError, UnauthorizedCommandError):
                    self.do_AI_reply(msg_with_nick, sender,
                                     no_delay=is_private, log_response=is_private)
            else:
                self.do_AI_reply(msg_with_nick, sender, no_delay=is_private,
                                 log_response=is_private)
        else:
            self.do_AI_maybe_reply(msg_with_nick, sender, log_response=False)

    def is_flooding(self, sender):
        if self.opts.flood_protect is None:
            return False

        interval, max_msgs, cooldown_interval = self.opts.flood_protect
        interval = datetime.timedelta(seconds=interval)
        cooldown_interval = datetime.timedelta(seconds=cooldown_interval)

        now = datetime.datetime.now()
        try:
            rate = self.user_message_rate[sender]
        except KeyError:
            rate = self.user_message_rate[sender] = {
                'first_msg_time': now,
                'last_msg_time': now,
                'msg_count': 0,
            }

        is_flooding = rate['msg_count'] > max_msgs
        interval_expired = False
        if is_flooding and now - rate['last_msg_time'] >= cooldown_interval:
            interval_expired = True
        elif not is_flooding and now - rate['first_msg_time'] >= interval:
            interval_expired = True
        if interval_expired:
            rate['first_msg_time'] = now
            rate['msg_count'] = 0
        rate['msg_count'] += 1

        is_flooding = rate['msg_count'] > max_msgs
        print('Flood protect: Now: {}    First msg: {}    Last msg: {}'.format(
            now, rate['first_msg_time'], rate['last_msg_time']))
        print('Flood protect: {}: Messages: {}    Is flooding: {}'.format(
            sender, rate['msg_count'], is_flooding))
        print('Flood protect: Interval: {}    Cooldown: {}'.format(
            interval.seconds, cooldown_interval.seconds))
        rate['last_msg_time'] = now
        return is_flooding

    def action(self, user, channel, msg):
        """Pass actions to AI like normal lines"""
        self.privmsg(user, channel, msg)

    def ctcpQuery(self, user, channel, messages):
        """Just log private CTCPs for the heck of it"""
        for tag, data in messages:
            if channel == self.nickname:
                print('[ctcpQuery] private CTCP {} from {}: {}'.format(
                    tag, user, data))
        irc.IRCClient.ctcpQuery(self, user, channel, messages)

    def noticed(self, user, channel, message):
        """Log private notices, too, but don't do anything else with them"""
        if channel == self.nickname:
            print('[noticed] private NOTICE from {}: {}'.format(user, message))

    def kickedFrom(self, channel, kicker, message):
        """On kick, automatically try to rejoin after a bit"""
        self.call_later(random.randint(5, 300), self.join, channel)

    def irc_unknown(self, prefix, command, parms):
        if command == "INVITE":
            if irc_lower(parms[1]) in self.opts.channels:
                self.join(irc_lower(parms[1]))
                print('[irc_unknown] Received invite to {}; trying to join'.format(parms[1]))
            else:
                print('[irc_unknown] Ignoring invite to unrecognized channel '
                      '{}'.format(parms[1]))
        elif command == "PONG":
            pass
        elif command == 'ERROR':
            print('[irc_unknown] Server-reported error: {0}'.format(
                parms[0]))
            self.transport.loseConnection()
        else:
            print('[irc_unknown] Unknown: {0}, {1}, {2}'.format(
                prefix, command, parms))

    ## Custom methods ##

    def call_later(self, delay, callable, *args, **kw):
        """Set up a scheduled call to the reactor while keeping track of it so
        we can clean it up properly when the IRC connection is lost or
        killed."""
        cl = reactor.callLater(delay, callable, *args, **kw)
        self.delayed_calls.append(cl)
        return cl

    def reclaim_nick(self):
        """Attempt to reclaim preferred nick (self.alterCollidedNick will
        set up this function to be called again later on failure)"""
        self.pending_nick_reclaim_timer = False
        if self.nickname != self.opts.nicks[0]:
            print('Attempting to change nick from {} to {}'.format(
                repr(self.nickname), repr(self.opts.nicks[0])))
            self.setNick(self.opts.nicks[0])
            self.set_nick_reclaim_timer()

    def set_nick_reclaim_timer(self):
        """Set up a timer to try to reclaim preferred nick, if one is not
        already set"""
        if not self.pending_nick_reclaim_timer:
            self.pending_nick_reclaim_timer = True
            self.call_later(self.opts.nick_retry_wait, self.reclaim_nick)

    def is_highlight(self, msg):
        """Check if msg contains an instance of bot's current nickname"""
        if re.search(r'\b{}\b'.format(re.escape(self.nickname)),
                     msg, flags=re.I):
            return True
        return False

    def preparse_msg(self, user, raw_msg):
        """Check message for certain IRC bridge bots; separate out correct
        nickname and return the message with non-Unicode characters
        replaced so they won't cause later problems."""
        nick, host = user.split('!', 1)
        msg = sanitize(strip_color(raw_msg)).strip()
        msg = msg.decode(encoding='utf8', errors='replace').encode(
            encoding='utf8')

        # Parse/convert saxjax's messages
        if hostmask_match('saxjax*!*@*', user):
            m = re.match(r'(?:\[.\] <(.*?)> (.*))', msg)
            if m:
                # Normal chat speaking
                nick = m.group(1)
                msg = m.group(2)
                if nick == 'Cemetech':
                    # ...or log ins/log outs/file uploads
                    m = re.match(r'(.*?) ((?:entered|logged|uploaded|deleted|added|edited).*)', msg)
                    if m:
                        nick = m.group(1)
                        msg = m.group(2)
        elif hostmask_match('BN-Relay*!*@*', user):
            m = re.match(r'<(.*?)> (.*)', msg)
            if m:
                nick, msg = m.group(1), m.group(2)
        elif (hostmask_match('*!~dragonlin@*', user) or
              hostmask_match('*!~RoccoLink@*', user)):
            m = re.match(r'\[(.*?)\] (.*)', msg)
            if m:
                nick, msg = m.group(1), m.group(2)
        return nick, msg

    def report_error(self, source, silent=False):
        """Log a traceback if NikkyAI fails due to an unhandled exception
        while generating a response, and respond with a random amusing line
        if silent is False"""
        if not silent:
            pub_reply = random.choice(
                ['<Oops>',
                 '<Ow, my head hurts>',
                 '<TEV YOU SCREWED YOUR CODE UP AGAIN>',
                 '<Sorry, lost my marbles for a second>',
                 '<I forgot what I was going to say>',
                 '<Crap, unhandled exception again>',
                 '<TEV: FIX YOUR CODE PLZKTHX>',
                 '<ERROR: Operation failed successfully!>',
                 "<Sorry, I find you too lame to give you a proper response>",
                 "<Houston, we've had a problem.>",
                 '<Segmentation fault>',
                 '<This program has performed an illegal operation and will '
                   'be prosecuted^H^H^H^H^H^H^H^H^H^Hterminated.>',
                 '<General protection fault>',
                 '<Guru Meditation #00000001.1337... wait, what? What kind of '
                   'system am I running on, anyway?>',
                 '<Nikky panic - not syncing: TEV SUCKS>',
                 '<This is a useless error message. An error occurred. '
                   'Goodbye.>',
                 '<HCF>',
                 '<ERROR! ERROR!>',
                 '<BSOD.png>',
                 '<Core dumped>',
                 '\001ACTION explodes due to an error\001']
            )
            # ...for even more humiliation if we're in one of DecBot's channels
            if (source in ('#cemetech', '#flood') and not
                    pub_reply.startswith('\001')):
                pub_reply = random.choice(['','!qadd ','~blame\n']) + pub_reply
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
            channel, chankey = args, irc_lower(args)
            self.opts.channels.add(chankey)
            self.join(channel)
            # Update preferred keywords/munges for new channel
            pk = set()
            ml = set()
            rnl = set()
            self.nikkies[chankey]   # Summon new channel NikkyAI into existence
            for nikky in self.nikkies.values():
                pk = pk.union(nikky.preferred_keywords)
                ml = ml.union(nikky.munge_list)
                rnl = rnl.union(nikky.replace_nicks_list)
            self.nikkies[chankey].preferred_keywords = pk
            self.nikkies[chankey].munge_list = ml
            self.nikkies[chankey].replace_nicks_list = rnl
            self.nikkies[chankey].save_state()

        elif cmd == '?part':
            if not is_admin:
                raise UnauthorizedCommandError
            channel, chankey = args, irc_lower(args)
            try:
                self.opts.channels.remove(chankey)
            except ValueError:
                pass
            self.part(channel)

        elif cmd == '?addword':
            if not is_admin:
                raise UnauthorizedCommandError
            for nikky in self.nikkies.values():
                nikky.add_preferred_keyword(args)
                self.notice(sender, '{}: Keyword added; {} total'.format(
                    nikky.id, len(nikky.preferred_keywords)))

        elif cmd == '?delword':
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

        elif cmd == '?addmunge':
            if not is_admin:
                raise UnauthorizedCommandError
            self._cmd_add_munge(args)
            self.notice(sender, 'Munge added: {}'.format(args))

        elif cmd == '?delmunge':
            if not is_admin:
                raise UnauthorizedCommandError
            self._cmd_delete_munge(args)
            self.notice(sender, 'Munge deleted: {}'.format(args))

        elif cmd == '?addreplace':
            if not is_admin:
                raise UnauthorizedCommandError
            for nikky in self.nikkies.values():
                nikky.add_replace_nick(args)
                self.notice(sender, '{}: Replace nick added: {} total'.format(
                    nikky.id, len(nikky.replace_nicks_list)))

        elif cmd == '?delreplace':
            if not is_admin:
                raise UnauthorizedCommandError
            for nikky in self.nikkies.values():
                try:
                    nikky.delete_replace_nick(args)
                except KeyError:
                    self.notice(sender, '{}: Nick not found'.format(
                        nikky.id))
                else:
                    self.notice(sender,
                                '{}: Nick removed; {} total'.format(
                                    nikky.id, len(nikky.replace_nicks_list)))

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
            usage_msg = 'Usage: botchat personality1 personality2'
            parms = args.split(' ')
            nikky = self.nikkies[None]
            if (len(parms) != 2 or
                    not nikky.is_personality_valid(parms[0]) or
                    not nikky.is_personality_valid(parms[1])):
                self.call_later(2, self.msg, sender, usage_msg)
                self.call_later(
                    4, self.msg, sender,
                    personalitiesrc.get_personality_list_text())
            else:
                nick1 = nikky.normalize_personality(parms[0])
                nick2 = nikky.normalize_personality(parms[1])
                if self.user_threads >= self.opts.max_user_threads:
                    self.call_later(
                        2, self.msg, sender,
                        "Sorry, I'm too busy at the moment. Please try again "
                        "later!")
                else:
                    self.call_later(
                        2, self.msg, sender,
                        "Generating the bot chat may take a while... I'll let "
                        "you know when it's done!")
                    d = threads.deferToThread(self.exec_bot_chat, src_nick,
                                              sender, nick1, nick2)
                    d.addErrback(self.bot_chat_error, sender)
                    d.addCallback(self.return_bot_chat)

        elif re.match((r"\b(quit|stop|don.?t|do not)\b.*\b(hilite|hilight|highlite|highlight).*\bme"), msg, re.I):
            self._cmd_add_munge(src_nick.lower())
            msg = "Sorry, {}, I'll stop (tell me 'highlight me' to undo)".format(self.nikkies[None].munge_word(src_nick))
            self.call_later(2, self.msg, sender, msg)

        elif re.match((r"\b(hilite|hilight|highlite|highlight) me"), msg,
                      re.I):
            self._cmd_delete_munge(src_nick.lower())
            msg = "Okay, {}!".format(src_nick)
            self.call_later(2, self.msg, sender, msg)

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
        self.call_later(2, self.msg, nick,
                          'Sorry, something went wrong. Tell tev!')
        self.user_threads -= 1
        assert(self.user_threads >= 0)
        return failure

    def do_AI_reply(self, msg, target, silent_errors=False, log_response=True,
                    no_delay=False):
        """Output an AI response for the given msg to target (user or channel)
        trapping for exceptions"""
        self._do_AI_reply(msg, target, self.opts.direct_response_time,
                          'reply', silent_errors, log_response, no_delay)

    def do_AI_maybe_reply(self, msg, target, silent_errors=True,
                          log_response=False):
        """Occasionally reply to the msg given, or say a random remark"""
        self._do_AI_reply(msg, target, self.opts.random_response_time,
                          'decide_remark', silent_errors, log_response, False)

    def _do_AI_reply(self, msg, target, search_time, reply_method_name,
                     silent_errors, log_response, no_delay):
        nikky = self.nikkies[irc_lower(target)]
        nikky.search_time = search_time
        context = ' '.join(nikky.last_lines)

        # Notify NikkyAIs in self.nikkies of the current nick.  Since
        # self.nikkies uses lazy instintiation, doing it just on nick
        # change events rather than here would mean that instances
        # created afterward would miss out on the memo.
        nikky.nick = self.nickname

        m = getattr(nikky, reply_method_name)
        try:
            reply = m(msg, context=context).split('\n')
        except Exception:
            self.report_error(target, silent_errors)
        else:
            if reply and log_response:
                print('privmsg to {}: {}'.format(target, repr(reply)))
            if reply:
                self.output_timed_msg(target, reply, no_delay=no_delay)

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
        self._schedule_output()

    def _schedule_output(self):
        """Set up delayed output message scheduling if it's not
        already running"""
        if not self.responses_scheduled:
            self.responses_scheduled = True
            self._output_next_scheduled_msg()

    def _output_next_scheduled_msg(self):
        """Schedule next pending line of output, then kick off a timed
        event to output it and then schedule the next one"""
        if self.pending_responses:
            time, target, msg = self.pending_responses.pop(0)
            self.call_later(time, self.msg, target,
                            self.escape_message(msg),
                            length=self.opts.max_line_length)
            self.call_later(time, self._output_next_scheduled_msg)
        else:
            self.responses_scheduled = False

    def escape_message(self, msg):
        """'Escape' a message by inserting an invisible control character
        at the beginning in some cases, to avoid triggering public bot
        commands."""
        if (msg[0] in '!?@#$%^&*-.,;:' and
                not msg.startswith('!qfind') and
                not msg.startswith('!karma')):
            return '\x0F' + msg
        else:
            return msg

    def reload_ai(self):
        rebuild(sys.modules['nikkyai'])
        for n in self.nikkies:
            state = self.nikkies[n].get_state()
            self.nikkies[n] = nikkyai.NikkyAI(id=n)
            self.nikkies[n].set_state(state)

    def channel_check(self):
        """Retry any channels that we apparently didn't successfully join for
        some reason."""
        for c in self.opts.channels:
            if irc_lower(c) not in self.joined_channels:
                self.join(c)
        self.call_later(self.opts.channel_check_interval, self.channel_check)

    def cleanup_state(self):
        """Clean up any stale state data to reduce memory and disk usage"""
        self.factory.cleanup_state()
        self.call_later(self.opts.state_cleanup_interval, self.cleanup_state)

