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

from _table import *
import nikkyai

def rule(nikky, context, fmt):
    # Do our own repeated response checking--this lets us avoid giving the same
    # “rule” more than once in the same list, even if several are being
    # combined at once into a single output message
    #
    # Caveat:  if this function's output is the only thing output in a table
    # rule, “allow repeats” flag *must* be True (even though repeats are still
    # avoided), else it will loop forever and never output anything (it will
    # check the response here, add it to the list, and then check it again
    # in nikkyai, which will always reject it as a duplicate before ever being
    # output).
    saved_search_time = nikky.search_time
    for i in xrange(0, nikky.recurse_limit):
        seed = choice(("Don't be", "Don't use", "Don't talk", "Don't bring",
                       "Don't mention", "Don't do", "Don't act", "Just kick",
                       "Just ban", "Don't forget to", "Just stop", "Stop",
                       "Go", "Get", "No more", "No * allowed", "Kick * in the",
                       "Use only", "Only use"))
        chain = nikky.markov.str_to_chain(seed, wildcard="*")
        nikky.search_time = 1
        out = nikky.markov_forward(chain, src_nick=fmt[0], context=context,
                                   max_lf=0)
        nikky.search_time = saved_search_time
        try:
            out = nikky.check_output_response(out, add_response=True)
        except nikkyai.Bad_response_error:
            continue
        return out
    return "<No workable quotes found…>"

def war(nikky, context, fmt):
    recurse_count = 0
    subject = ''
    while not subject.strip():
        recurse_count += 1
        if recurse_count > nikky.recurse_limit:
            return 'Are we arguing about random crap again?!'

        verb = choice(('arguing', 'bitching', 'complaining', 'yelling',
                       'shouting'))
        chain = (verb, 'about')
        subject = nikky.markov_forward(chain, context=context, src_nick=fmt[0])
        if not subject.strip():
            continue
        subject = subject.replace('\n', '... ')

        # Cut off starting at first word that ends with punctuation
        chain = subject.split()
        for last_word, word in enumerate(chain):
            if last_word < 2:
                # Don't consider first two chain words ("… about"); they
                # don't count
                continue
            if not word[-1].isalnum():
                break
        last_word += 1
        chain = chain[0:last_word]
        subject = ' '.join(chain)
        # Remove certain punctuation/nonalphanumerics from end of subject
        while (subject.strip() and not subject[-1].isalnum()
               and not subject[-1] in '\'"[]{}'):
            subject = subject[:-1]
        # Remove first two words (the Markov chain) from subject
        chain = subject.split()
        chain = chain[2:]
        # If chain is now empty, need to start over and try again using a
        # different phrase
        if not chain:
            continue
        # Don't repeat the word "again"
        if chain[-1].lower() == 'again':
            chain = chain[:-1]
        # Reconstruct the subject string, force beginning word to lowercase
        subject = ' '.join(chain)
        subject = subject[0].lower() + subject[1:]
    # Return it
    return 'Are we arguing about ' + subject + ' again?'


# General patterns used for all personalities, including 'nikky'

patterns = (
# Legal forms:
# pattern regexp, priority, action
# pattern regexp, priority, action, allow repeat?
# pattern regexp, last reply, priority, action, allow repeat?

## Basics ##

(r"\b(hi|hello|hey|sup|what'?s up|welcome)\b", 50,
    R(
        Markov_forward('{1}'),
        Markov_forward('{1} {0}'),
        '{1}, {0}',
    ),
),
(r"\b(how are you|how are we|how'?s your|how is your)\b", 49,
    R(
        Markov_forward('ok', force_completion=False),
        Markov_forward('okay', force_completion=False),
        Markov_forward('good', force_completion=False),
        Markov_forward('bad', force_completion=False)
    ),
),
(r"\b(good night|goodnight|g'?night)\b", 50,
    R(
        Markov_forward('night', force_completion=False),
        Markov_forward('night {0}', force_completion=False),
    )
),
(r"\b(bye|bye bye|goodbye|good bye|see you later|cya|see ya|night|good night|g'night|gtg|brb|bbl)\b", 50,
    R(
        Markov_forward('bye', force_completion=False),
        Markov_forward('bye {0}', force_completion=False)
    ),
),
(r"\b(congratulations|congrats|congradulations)", 51,
    R(
        Markov_forward('Thanks', force_completion=False),
        Markov_forward('thx', force_completion=False),
    )
),
(r'\b(thanks|thank you)\b', 51,
    R(
        Markov_forward("you're welcome", force_completion=False),
        'np'
    )
),
(r'\b(wb|welcome back|welcoem back)\b', 51,
    R(
        Markov_forward('Thanks', force_completion=False),
        Markov_forward('thx', force_completion=False),
    )
),
(r"\*\*\*yes/no\*\*\*", -99,
    R(
        Markov_forward('yes', force_completion=False),
        Markov_forward('no', force_completion=False),
        Markov_forward('maybe', force_completion=False),
        Markov_forward('yeah', force_completion=False),
        Markov_forward('probably', force_completion=False),
        Markov_forward('only if'),
        Markov_forward('only when'),
        Markov_forward('as long as'),
        Markov_forward('whenever', force_completion=False),
        Markov_forward('of course', force_completion=False),
        Markov_forward('depends', force_completion=False),
    )
),
(r"\b(yes|yah|yeah|right|naturally|of course|good|excellent|sure|exactly|definitely|absolutely|indeed|i agree|we agree|agreed)\b", 1,
    R(
        Markov_forward('well'),
        Markov_forward('okay, well'),
        Markov_forward('thanks', force_completion=False),
        Markov_forward('good idea', force_completion=False),
        Markov_forward('see, I told you', force_completion=False),
        Markov_forward('okay', force_completion=False),
        Markov_forward('right', force_completion=False),
        Markov_forward('nope', force_completion=False),
        Markov_forward('no', force_completion=False),
        Markov_forward('wrong', force_completion=False),
        "I'm glad we agree."
    ),
),
(r"\b(no|nope|nuh-uh|you aren'?t)\b", 1,
    R(
        Markov_forward('well'),
        Markov_forward('okay, well'),
        Markov_forward('then'),
        Markov_forward('whatever', force_completion=False),
        Markov_forward('yes', force_completion=False),
        Markov_forward('then * you', force_completion=False),
        Markov_forward('well * you', force_completion=False),
        Markov_forward('well * you then', force_completion=False),
        Markov_forward('* you', force_completion=False),
        Markov_forward('* you then', force_completion=False),
    ),
),
(r"^(but|don'?t)\b", 0,
    R(
        Markov_forward('well'),
        Markov_forward('okay, well'),
        Markov_forward('then'),
        Markov_forward('whatever', force_completion=False),
        Markov_forward('good idea', force_completion=False),
        Markov_forward('okay', force_completion=False),
        Markov_forward('right', force_completion=False),
        Markov_forward('nope', force_completion=False),
        Markov_forward('no', force_completion=False),
        Markov_forward('so', force_completion=False),
        Markov_forward('why', force_completion=False),
    ),
),

## Questions ##

(r"which", 1,
    R(
        Markov_forward('this'),
        Markov_forward('that'),
        Markov_forward('the'),
        Markov_forward('those', force_completion=False),
        Markov_forward('these', force_completion=False),
        Markov_forward('all of'),
        Markov_forward('all the'),
    ),
),
(r"anything else", 1,
    S(
        R('', Recurse('***yes/no***')),
        '\n',
        Recurse("what's"),
    ),
),
(r"(what do you|what is going|what'?s going)", -2,
    Recurse('what are you doing')
),
(r"(what is|what'?s) (a|the) (\w+) (\w+)", -1,
    R(
        Markov('is a * {4}'),
        Markov('is the * {4}'),
        Markov('is a {3} {4}'),
        Markov('is the {3} {4}'),
        Markov('a * {4} is'),
        Markov('the * {4} is'),
        Markov('a {3} {4} is'),
        Markov('the {3} {4} is'),
    ),
),
(r"(what|what'?s|for which)", 1,
    R(
        Markov_forward('a'),
        Markov_forward('an'),
        Markov_forward('the'),
        Markov_forward("It's a"),
        Markov_forward("It's an"),
        Markov_forward("It's the"),
        Markov_forward("It is a"),
        Markov_forward("It is an"),
        Markov_forward("It is the"),
        Recurse('how many'),
    ),
),
(r"(who is|who'?s|what is|what'?s|how'?s|how is) (the |a |an |your |my )?(\w+)", 0,
    R(
        Markov_forward('{3} is'),
        Markov_forward('{3}'),
        Markov_forward('A {3} is'),
        Markov_forward('An {3} is'),
        Markov_forward('The {3} is'),
        Markov_forward('A {3}'),
        Markov_forward('An {3}'),
        Markov_forward('The {3}'),
        Recurse("what's"),
    ),
),
(r"(who are|who'?re|what are|what'?re|how'?re|how are) (\w+)", 0,
    R(
        Markov_forward('{2} are'),
        Markov_forward("They're"),
        Markov_forward('They are'),
    ),
),
(r"(what are|what'?re) .*ing\b", -1,
    Recurse("what's"),
),
(r'where\b', 0,
    R(
        Markov_forward('in'),
        Markov_forward('on'),
        Markov_forward('on top of'),
        Markov_forward('inside of'),
        Markov_forward('inside', force_completion=False),
        Markov_forward('under'),
        Markov_forward('behind'),
        Markov_forward('outside', force_completion=False),
        Markov_forward('over', force_completion=False),
        Markov_forward('up', force_completion=False),
        Markov_forward('beyond', force_completion=False),
    )
),
(r'when\b', 1,
    R(
        'never',
        'forever',
        'right now',
        'tomorrow',
        'now',
        Markov_forward('never', force_completion=False),
        Markov_forward('tomorrow', force_completion=False),
        Markov_forward('as soon as'),
        Markov_forward('whenever', force_completion=False),
        Markov_forward('after'),
        Markov_forward('before'),
        Markov_forward('yesterday', force_completion=False),
        Markov_forward('last'),
        Markov_forward('next'),
    )
),
(r'how\b', 1,
    R(
        Markov_forward('by'),
        Markov_forward('via'),
        Markov_forward('using'),
        Markov_forward('use'),
        Markov_forward('only by'),
        Markov_forward('only by using'),
        Markov_forward('just use'),
    )
),
(r'how (long|much longer|much more time)\b', -2,
    R(
        'never',
        'forever',
        Markov_forward('until'),
        Markov_forward('as soon as'),
        Markov_forward('whenever'),
    )
),
(r'\b(how much|how many|what amount|how .* is)\b', -2,
    R(
        Markov_forward('enough', force_completion=False),
        Markov_forward('too many', force_completion=False),
        Markov_forward('more than you', force_completion=False),
        Markov_forward('not enough', force_completion=False),
    )
),
(r'\b(what|who) (are you|is {0}) doing\b', -1,
    R(
        Markov_forward("I'm"),
        Markov_forward("I am"),
    ),
),
(r'\bwho am I\b', -1,
    R(
        Markov_forward("You're a"),
        Markov_forward('You are a'),
        Markov_forward("You're an"),
        Markov_forward('You are an'),
        Markov_forward("You're the"),
        Markov_forward('You are the'),
        'nobody', 'somebody', 'everybody', 'anybody',
        Markov_forward('nobody that'),
        Markov_forward('somebody that'),
        Markov_forward('everybody that'),
        Markov_forward('anybody that'),
        Markov_forward('nobody who'),
        Markov_forward('somebody who'),
        Markov_forward('everybody who'),
        Markov_forward('anybody who'),
    ),
),
(r'\bwho\b', 0,
    R(
        'nobody', 'somebody', 'everybody', 'anybody',
        Markov_forward('nobody that'),
        Markov_forward('somebody that'),
        Markov_forward('everybody that'),
        Markov_forward('anybody that'),
        Markov_forward('nobody who'),
        Markov_forward('somebody who'),
        Markov_forward('everybody who'),
        Markov_forward('anybody who'),
    )
),
(r'\b(why|how come)\b', 0,
    R(
        Markov_forward('because', force_completion=False),
        Markov_forward('because your'),
        Markov_forward('because you'),
        Markov_forward('because of'),
        Markov_forward('because of your')
    )
),
(r'\bwhat does it mean\b', 1,
    Markov_forward('it means')
),
(r'\b(who|what) (does|do|did|should|will|is) (\w+) (\w+)', 0,
    R(
        Recurse('which'),
        Markov_forward('{3} {4}'),
        Markov_forward('{3} {4}s'),
    ),
),
(r"(\S+)\s+(\S+)\s+(what|who|whom|which)\b", -2, Markov_forward('{1} {2}')),
(r"(\S+)\s+(what|who|whom|which)\b", -1, Markov_forward('{1}')),

(r"\b(is|isn'?t|are|am|does|should|would|can|do|did)\b", 2,
    Recurse('***yes/no***')
),
(r'\b(do you think|what about|really)\b', 0, R(Recurse('***yes/no***'))),
(r"\b(is|are|am|should|would|can|do|does|which|what|what'?s|who|who'?s)(?: \S+)+[ -](.*?)\W+or (.*)\b", -1,
    S(
        R(
            'both',
            'neither',
            'dunno',
            S('{2}', R('--', '? ', ': ', '\n'), Recurse('what do you think of {2}')),
            S('{3}', R('--', '? ', ': ', '\n'), Recurse('what do you think of {3}'))
        ),
        '\n',
        R('', Markov_forward('because', [' ']), Markov_forward('since', [' '])),
    ),
),
(r'\bwhat time\b', 0,
    R(
        Markov_forward('time for'),
        Markov_forward("it's time"),
    ),
),
(r"\b(will|should|can|going to|won'?t|wouldn'?t|would|can'?t|isn'?t|won'?t) (\w+)\b", 5,
    R(
        Markov_forward('and'),
        Markov_forward('and just'),
        Markov_forward('and then'),
        Markov_forward('and then just'),
        Markov_forward('or'),
        Markov_forward('or just'),
        Markov_forward('yes and'),
        Markov_forward('yes or'),
        Markov_forward('yeah and'),
        Markov_forward('yes and'),
        Markov_forward('yes and just'),
        Markov_forward('yes or just'),
        Markov_forward('yeah and just'),
        Markov_forward('yes and just'),
        Markov_forward('and {2}'),
        Markov_forward('and just {2}'),
        Markov_forward('and then {2}'),
        Markov_forward('and then just {2}'),
        Markov_forward('or {2}'),
        Markov_forward('or just {2}'),
        Markov_forward('yes and {2}'),
        Markov_forward('yes or {2}'),
        Markov_forward('yeah and {2}'),
        Markov_forward('yes and {2}'),
        Markov_forward('yes and just {2}'),
        Markov_forward('yes or just {2}'),
        Markov_forward('yeah and just {2}'),
        Markov_forward('yes and just {2}'),
        Markov_forward('why', force_completion=False),
    ),
),
(r"\b(really|orly|rly)\b", 0, Recurse('***yes/no***')),
(r"\b(((tell|tell us|tell me|say) (something|anything)|gossip)|(what's .*\b(new|news)))", -12,
    R(
        Markov_forward('did you know', order=3),
        Markov_forward('fun fact', order=3),
        Markov_forward('I heard', order=3),
        Markov_forward('I hear', order=3),
        Markov_forward('a recent study', order=3),
        Markov_forward('guess what', order=3),
    )
),

## Misc ##

(r'\bcontest\b', 1,
    R(
        Recurse("I'm entering"),
        Recurse("You'll lose"),
        Recurse('My entry'),
        Markov_forward('Contests'),
        Markov('contest')
    )
),
(r'\b(talk|discuss|mention|topic|off-topic)', -11,
    R(
        Markov_forward("Let's discuss"),
        Markov_forward("Let's talk about"),
    ),
),

## Meta ##

(r'(Do )?you (like|liek) (.*)(.*?)\W?$', -1,
    R(
        Recurse('what do you think about {3}'),
        Recurse('yes'),
        S(
            R('', 'No, but ', 'Yes, and '),
            Markov_forward('I like'),
        ),
        Markov_forward("I'd rather"),
        'of course'
    )
),
(r'^(\S+ (u|you|{0})$|(\bWe |\bI )\S+ (u|you|{0}))', 5,
    S(
        R('Great\n', 'gee\n', 'thanks\n', 'Awesome\n', 'yay\n', 'wow\n'),
        R(
            Markov_forward('I wish you'),
            Markov_forward('I hope you'),
            Markov_forward('I hope your'),
            Markov_forward('You deserve'),
            Markov_forward("You don't deserve"),
            Markov_forward('TIL'),
            Markov_forward('I know'),
            Markov_forward('I knew'),
            Markov_forward("I'm sure"),
            Markov_forward("That's why"),
            Markov_forward("That's what"),
            Markov_forward("And I'm"),
            Markov_forward("And I bet"),
            Markov_forward("I didn't know"),
            Markov_forward("Did you know"),
            Markov_forward("And did you know"),
        ),
    ),
),
(r'\b({0} is|you are|{0} must|you must) (a |an |)(.*)', 1,
    R(
        Markov_forward('I am'),
        Markov_forward("I'm"),
        Markov_forward('I am really'),
        Markov_forward("I'm really"),
        Markov_forward('I am actually'),
        Markov_forward("I'm actually"),
    )
),
(r"\b(?:what do you (?:think|thing)|what do you know|tell us about|tell me about|how (?:do|did|will) you feel|(?:what is |what'?s |what are )?your (?:thought|thoughts|opinion|opinions|idea|ideas)) (?:about |of |on )(?:a |the |an )?(.*?)\W?$", -3,
    R(
        Markov_forward('{1} is'),
        Markov_forward('{1}'),
        Markov_forward('{1} is'),
        Markov_forward('{1}'),
        Markov_forward('{1} is'),
        Markov_forward('{1}'),
        Markov_forward('better than'),
        Markov_forward('worse than'),
    ),
),
(r"\bis (.*?) (any good|good)", 0, Recurse('what do you think of {1}')),
(r"^(what do you (think|thing)|what do you know|tell us about|tell me about|how (do|did|will) you feel|(what is|what'?s|what are) your (thought|thoughts|opinion|opinions|idea|ideas)) (about |of |on )me\W?$", -3,
    R(
        Markov_forward('you'),
        Recurse('what do you think of {0}')
    )
),
(r"^(how is|how'?s|do you like|you like|you liek) (.*?)\W?$", -3,
    Recurse('what do you think of {2}')
),
(r"\btell (me|us) about (.*)", -2, Recurse('{2}')),
(r'(what|who)(|.s|s)? (is )?(your|{0})(.s|s)? (.*?)$', -2,
    R(
        Markov_forward('my {6} is'),
        Markov_forward('my {6} was'),
        Markov_forward('my {6} will'),
        Markov_forward("my {6} isn't"),
        Markov_forward('my {6} is not'),
        Markov_forward("my {6} won't"),
        Markov_forward("my {6} can't"),
        Markov_forward('my {6}'),
        Markov_forward('the {6}'),
    )
),
(r'(what|who)(|.s|s)? (is )?(the|your|{0})(.s|s)? (favorite|favorit|preferred) (.*?)( of choice)?$', -5,
    R(
        Markov_backward('favorite {7}'),
        Markov_backward('best {7}'),
        Markov_backward('superior {7}'),
        Markov_backward('coolest {7}'),
        Markov_backward('only {7}'),
        Markov_backward('greatest {7}'),
        Markov_backward('most awesome {7}'),
    ),
),

## Special ##

(r'\brule\b', -1, E(rule), True),
    #                     ^ Not really allowing repeats (already handled by
    # (rule function; if this is False, it will double-check and fail every
    # response as a duplicate and never output anything.)
(r'\brules\b', -1,
    S(
        R('Rules:', 'Channel rules:', 'Forum rules:', "Today's rules",
          "Today's channel rules:", "Today's forum rules:"),
        '\n1. ', E(rule),
        '\n2. ', E(rule),
        '\n3. ', E(rule),
    )
),
(r'\b(war|wars)[0-9]*\b', 0, E(war)),

## Markov search/debug ##

(r'^\??markov5 (.*)', -99, Manual_markov(5, '{1}'), True),
(r'^\??markov4 (.*)', -99, Manual_markov(4, '{1}'), True),
(r'^\??markov3 (.*)', -99, Manual_markov(3, '{1}'), True),
(r'^\??markov2 (.*)', -99, Manual_markov(2, '{1}'), True),
(r'^\??markov5nr (.*)', -99, Manual_markov(5, '{1}'), False),
(r'^\??markov4nr (.*)', -99, Manual_markov(4, '{1}'), False),
(r'^\??markov3nr (.*)', -99, Manual_markov(3, '{1}'), False),
(r'^\??markov2nr (.*)', -99, Manual_markov(2, '{1}'), False),
(r'^\??markov5f (.*)', -99, Manual_markov_forward(5, '{1}'), True),
(r'^\??markov4f (.*)', -99, Manual_markov_forward(4, '{1}'), True),
(r'^\??markov3f (.*)', -99, Manual_markov_forward(3, '{1}'), True),
(r'^\??markov2f (.*)', -99, Manual_markov_forward(2, '{1}'), True),
(r'^\??markov5fnr (.*)', -99, Manual_markov_forward(5, '{1}'), False),
(r'^\??markov4fnr (.*)', -99, Manual_markov_forward(4, '{1}'), False),
(r'^\??markov3fnr (.*)', -99, Manual_markov_forward(3, '{1}'), False),
(r'^\??markov2fnr (.*)', -99, Manual_markov_forward(2, '{1}'), False),

)
