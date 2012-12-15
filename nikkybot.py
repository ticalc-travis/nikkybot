#!/usr/bin/env python3

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

# TODO:
#   - LurkLib is proving unreliable and buggy.  Probably need to find a
#     different IRC/bot lib and port to that

import lurklib
import lurklib.exceptions
from nikkyai import NikkyAI

from imp import reload
from os import uname
import sched
import socket
import random
import re
import sys
from time import time, sleep, strftime
import traceback

# === CONFIGURATION SECTION ===========================================

SERVERS = (
    # (Name, port, use tls?)
    ('irc.choopa.net', 6667, False),
    ('efnet.port80.se', 6667, False),
    ('irc.eversible.net', 6667, False),
    ('irc.shoutcast.com', 6667, False),
# Buggy/problematic servers; do not use
#    ('irc.teksavvy.ca', 6667, False),
#    ('irc.paraphysics.net', 6667, False),
#    ('irc.he.net', 6667, False),
)
REAL_NAME = 'NikkyBot'
NICKS = ('nikkybot', 'nikkybot2', 'nikkybot_')
CHANNELS = ('#tcpa', '#flood', '#cemetech')    # “Production” mode
#CHANNELS = ('#flood',)   # Test only mode
CLIENT_VERSION = \
    "Lurklib bot (contact 'tev' or travisgevans@gmail.com):{}:{} {}".format(
        lurklib.__version__, uname()[0], uname()[4])
ADMIN_HOSTMASKS = ('*!ijel@ip68-102-86-156.ks.ok.cox.net',
                   '*!travise@nvm2u.com',
                   '*!travise@64.13.172.47')
MIN_SEND_TIME = 1   # seconds
RECONNECT_WAIT = 10    # seconds
NICK_RETRY_WAIT = 300    # seconds
SIMULATED_TYPING_SPEED = .1    # seconds/character

# === END CONFIGURATION SECTION =======================================

requestedShutdown = False

class NikkyDict(dict):
    def __missing__(self, key):
        self[key] = NikkyAI()
        return self[key]
        
        
class NikkyBot(lurklib.Client):
    def __init__(self, *args, **kwargs):
        self.scheduler = sched.scheduler(time, self.mainloopDelay)
        self.lastSchedTime = time()
        self.nikkies = NikkyDict()
        lurklib.Client.__init__(self, *args, **kwargs)
        
    def join_(self, channel, key=None, process_only=False):
        print('Joining {}'.format(channel))
        lurklib.Client.join_(self, channel, key, process_only)
        
    def privmsg(self, target, message):
        try:
            if message:
                lurklib.Client.privmsg(self, target, '\x0F' + message)
        except self.CannotSendToChan as e:
            print('WARNING: Cannot send to channel')
            print(e)
        
    def nick(self, nick):
        lurklib.Client.nick(self, nick)
        for n in self.nikkies:
            self.nikkies[n].nick = nick
        
    def queue(self, timeToRun, function, args, priority=1):
        self.scheduler.enter(max(timeToRun, MIN_SEND_TIME), priority,
            function, args)
            
    def mainloopDelay(self, seconds):
        if seconds > 0:
            self.mainloop(seconds)
        else:
            self.mainloop(1)
            
    def respondLines(self, target, lines):
        last = 0
        for l in lines:
            t = 3 + len(l) * SIMULATED_TYPING_SPEED
            self.queue(last + t, self.privmsg, (target, l))
            last += t

    def run(self):
        while self.keep_going:
            if self.scheduler.empty():
                self.mainloop(1)
            else:
                self.scheduler.run()
                
    def quit(self):
        requestedShutdown = True
        lurklib.Client.quit()
        
    def mainloop(self, duration=None):
        if duration is None:
            lurklib.Client.mainloop(self)
        elif duration > 0:
            with self.lock:
                if self.on_connect and not self.readable(2):
                    self.on_connect()
                    self.on_connect = None
            self.process_once(duration)
            
    def tryReclaimNick(self):
        try:
            self.nick(NICKS[0])
        except self.NicknameInUse:
            self.queue(NICK_RETRY_WAIT, self.tryReclaimNick, ())
            
    def hostmaskMatch(self, testmask, knownmask):
        testmask = \
            testmask.replace('.', '\\.').replace('?', '.').replace('*', '.*')
        return re.match(testmask, knownmask)
        
    def anyHostmaskMatch(self, testmasks, knownmask):
        for mask in testmasks:
            if self.hostmaskMatch(mask, knownmask):
                return True
        return False
        
    def isHighlight(self, msg):
        return re.search(r'\b{}\b'.format(re.escape(self.current_nick)),
            msg, flags=re.I)
            
    def reportError(self, source, silent=False):
        if not silent:
            pubReply = random.choice(['Oops', 'Ow, my head hurts', 'TEV YOU SCREWED YOUR CODE UP AGAIN', 'Sorry, lost my marbles for a second', 'I forgot what I was going to say', 'Crap, unhandled exception again', 'TEV: FIX YOUR CODE PLZKTHX'])
            self.privmsg(source, pubReply)
        print()
        traceback.print_exc()
        print()
    
    def on_connect(self):
        print('Connection established.')
        for c in CHANNELS:
            self.queue(2, self.join_, (c,))
        if self.current_nick != NICKS[0]:
            self.queue(NICK_RETRY_WAIT, self.tryReclaimNick, ())
        for k in self.nikkies:
            self.nikkies[k].nick = self.current_nick

    def on_privctcp(self, from_, message):
        if message == 'VERSION':
            self.notice(from_[0],
                self.ctcp_encode('VERSION {}'.format(CLIENT_VERSION)))
        else:
            m = re.match('ACTION (.*)', message)
            if m:
                self.on_privmsg(from_,
                    '*{} {}'.format(from_[0], m.group(1)))
                    
    def on_chanctcp(self, from_, channel, message):
            m = re.match('ACTION (.*)', message)
            if m:
                self.on_chanmsg(from_, channel,
                    '*{} {}'.format(from_[0], m.group(1)))

    def on_chanmsg(self, from_, channel, message):
        nick = from_[0]
        hostmask = '{}!{}@{}'.format(*from_)
        fullMsg = '<{}> {}'.format(nick, message)
        if re.match('saxjax!~saxjax@.*ip\-142\-4\-211\.net', hostmask):
            m = re.match(r'\(.\) \[(.*)\] (.*)', message)
            if m:
                nick = m.group(1)
                fullMsg = '<{}> {}'.format(nick, m.group(2))
            else:
                m = re.match(r'\(.\) \*(.*?) (.*)', message)
                if m:
                    nick = m.group(1)
                    fullMsg = '<{}> {}'.format(nick, m.group(2))
        if self.isHighlight(message):
            try:
                self.respondLines(channel,
                    self.nikkies[channel].reply(fullMsg))
            except:
                self.reportError(channel)
        else:
            try:
                out = self.nikkies[channel].decideRemark(fullMsg)
                if out:
                    self.respondLines(channel, out)
            except:
                self.reportError(channel, silent=True)
            
    def on_privmsg(self, from_, message):
        nick = from_[0]
        hostmask = '{}!{}@{}'.format(*from_)
        fullMsg = '<{}> {}'.format(nick, message)
        print("{}: privmsg {}: {}".format(strftime('%Y-%m-%d %H:%M:%S'),
            hostmask, message))
        if self.anyHostmaskMatch(ADMIN_HOSTMASKS, hostmask):
            if message.rstrip() == '?quit':
                self.quit('Shutdown initiated')
                return
            elif message.startswith('?quit'):
                self.quit(message[len('?quit')+1:])
                return
            elif message.rstrip() =='?reload':
                # Reload AI-related module stuff
                try:
                    reload(sys.modules['nikkyai'])
                    from nikkyai import NikkyAI
                except Exception as e:
                    self.notice(nick, 'Reload error: {}'.format(e))
                else:
                    for k in self.nikkies:
                        lastReplies = self.nikkies[k].lastReplies
                        self.nikkies[k] = NikkyAI()
                        self.nikkies[k].lastReplies = lastReplies
                        self.nikkies[k].nick = self.current_nick
                    self.notice(nick, 'Reloaded nikkyai')
                return
            elif message.startswith('?code '):
                try:
                    exec(message[6:])
                except Exception as e:
                    self.notice(nick, 'Error: {}'.format(e))
                return
        try:
            replyText = self.nikkies[hostmask].reply(fullMsg)
            self.respondLines(nick, replyText)
            print("{}: privmsg response to {}: {}".format(
                strftime('%Y-%m-%d %H:%M:%s'), hostmask, replyText))
        except:
            self.reportError(nick)



if __name__ == '__main__':
    while True:
        uri, port, tls = random.choice(SERVERS)
        print('Connecting to {}...'.format(uri))
        try:
            bot = NikkyBot(server=uri, port=port, nick=NICKS,
                           tls=tls, real_name=REAL_NAME)
            bot.run()
        except Exception as e:
            print(e)
            if not requestedShutdown:
                print('Unhandled exception, restarting in {} seconds'.format(
                    RECONNECT_WAIT))
                sleep(RECONNECT_WAIT)
            else:
                break
        else:
            if requestedShutdown:
                break
            print("Something happened; we quit but weren't supposed to")
            print('Restarting in {} seconds'.format(RECONNECT_WAIT))
            sleep(RECONNECT_WAIT)
            

