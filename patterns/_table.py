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

# Pattern table objects

from random import choice

DEBUG = 1

MAX_LF_L = 1
MAX_LF_R = 2

class S(list):
    """Sequence table"""
    def __init__(self, *args):
        self.msg = ''
        self.match = None
        list.__init__(self, args)

    def get(self, fmt=None):
        s = ''
        for i in self:
            try:
                s += i.get(fmt)
            except AttributeError:
                s += i.format(*fmt)
        return s


class R(S):
    """Random table"""
    def get(self, fmt=None):
        i = choice(self)
        try:
            return i.get(fmt)
        except AttributeError:
            return i.format(*fmt)


class E(str):
    """Evaluate string"""
    def get(self, fmt=None):
        if fmt is None:
            fmt = []
        return str(eval(self.format(*fmt))).format(*fmt)


class Markov_forward(object):
    """Return a Markov chain from word or chain forward"""
    def __init__(self, string, failmsglist=None, max_lf_r=MAX_LF_R):
        self.chain = string.split(' ')
        self.max_lf_r = max_lf_r
        if failmsglist is None:
            failmsglist = ['']
        self.failmsglist = failmsglist

    def get(self, fmt=None):
        if fmt is None:
            fmt = []
        failmsg = choice(self.failmsglist)
        if DEBUG:
            print("DEBUG: Markov_forward.get: {}: {}".format(
                repr(self.chain), repr(fmt)))
        try:
            failmsg = failmsg.get(fmt)
        except AttributeError:
            pass
        return markov_forward([x.format(*fmt) for x in self.chain],
            failmsg, self.max_lf_r)


class Manual_markov(object):
    """Return a Markov-generated phrase of the given order"""
    def __init__(self, order, text):
        self.order = order
        self.text = text

    def get(self, fmt=None):
        if fmt is None:
            fmt = []
        return manual_markov(self.order, self.text.format(*fmt))


class Manual_markov_forward(object):
    """Return a Markov-generated phrase of the given order forward in
    context"""
    def __init__(self, order, text):
        self.order = order
        self.text = text

    def get(self, fmt=None):
        if fmt is None:
            fmt = []
        return manual_markov_forward(self.order, self.text.format(*fmt))


class Markov(object):
    """Force standard Markov processing on the given message and return
    result, even if message would otherwise match another regexp pattern"""
    def __init__(self, text, failmsglist=None):
        if failmsglist is None:
            failmsglist = ['']
        self.failmsglist = failmsglist
        self.text = text

    def get(self, fmt=None):
        if fmt is None:
            fmt = []
        failmsg = choice(self.failmsglist)
        try:
            failmsg = failmsg.get(fmt)
        except AttributeError:
            pass
        return markov_reply(self.text.format(*fmt), failmsg)


class Recurse(str):
    """Recursively find a response"""
    def get(self, fmt=None):
        if fmt is None:
            fmt = []
        try:
            return pattern_reply(self.format(*fmt))[0]
        except (Dont_know_how_to_respond_error, RuntimeError):
            for i in xrange(RECURSE_LIMIT):
                reply = markov_reply(self.format(*fmt))
                if reply.strip():
                    return reply
            return random_markov()
