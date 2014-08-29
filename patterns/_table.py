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


class S(list):
    """Sequence table"""
    def __init__(self, *args):
        self.msg = ''
        self.match = None
        list.__init__(self, args)

    def get(self, nikkyai, fmt=None):
        s = ''
        for i in self:
            try:
                s += i.get(nikkyai, fmt)
            except AttributeError as e:
                if str(e).endswith("'get'"):
                    s += i.format(*fmt)
                else:
                    raise e
        return s


class R(S):
    """Random table"""
    def get(self, nikkyai, fmt=None):
        i = choice(self)
        try:
            return i.get(nikkyai, fmt)
        except AttributeError as e:
            if str(e).endswith("'get'"):
                return i.format(*fmt)
            else:
                raise e


class E(object):
    """Run a given function and return its output"""
    def __init__(self, func):
        self.foreign_func = func

    def get(self, nikkyai, fmt=None):
        if fmt is None:
            fmt = []
        return self.foreign_func(nikkyai, fmt)


class Markov_forward(object):
    """Return a Markov chain from word or chain forward"""
    def __init__(self, string, failmsglist=None, max_lf=None,
                 force_completion=True):
        self.string = string
        if failmsglist is None:
            failmsglist = ['']
        self.failmsglist = failmsglist
        self.max_lf=max_lf
        self.force_completion = force_completion

    def get(self, nikkyai, fmt=None):
        if fmt is None:
            fmt = []
        failmsg = choice(self.failmsglist)
        try:
            failmsg = failmsg.get(nikkyai, fmt)
        except AttributeError:
            failmsg = failmsg.format(*fmt)
        chain = nikkyai.markov.str_to_chain(
            self.string.format(*fmt), wildcard='*')
        return nikkyai.markov_forward(chain, failmsg, max_lf=self.max_lf,
                                      force_completion=self.force_completion)


class Manual_markov(object):
    """Return a Markov-generated phrase of the given order"""
    def __init__(self, order, text):
        self.order = order
        self.text = text

    def get(self, nikkyai, fmt=None):
        if fmt is None:
            fmt = []
        return nikkyai.manual_markov(self.order, self.text.format(*fmt))


class Manual_markov_forward(object):
    """Return a Markov-generated phrase of the given order forward in
    context"""
    def __init__(self, order, text):
        self.order = order
        self.text = text

    def get(self, nikkyai, fmt=None):
        if fmt is None:
            fmt = []
        return nikkyai.manual_markov_forward(self.order,
                                             self.text.format(*fmt))


class Markov(object):
    """Force standard Markov processing on the given message and return
    result, even if message would otherwise match another regexp pattern"""
    def __init__(self, text, failmsglist=None):
        if failmsglist is None:
            failmsglist = ['']
        self.failmsglist = failmsglist
        self.text = text

    def get(self, nikkyai, fmt=None):
        if fmt is None:
            fmt = []
        failmsg = choice(self.failmsglist)
        try:
            failmsg = failmsg.get(fmt)
        except AttributeError:
            failmsg = failmsg.format(*fmt)
        return nikkyai.markov_reply(
            self.text.format(*fmt), add_response=False, failmsg=failmsg)


class Recurse(str):
    """Recursively find a response"""
    def get(self, nikkyai, fmt=None):
        if fmt is None:
            fmt = ['']
        return nikkyai.reply('<{}> {}'.format(
            fmt[0], self.format(*fmt)), add_response=False)
