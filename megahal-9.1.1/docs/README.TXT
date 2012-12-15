+----------------------------------------------------------------------------+
|                                                                            |
|    #    #  ######   ####     ##    #    #    ##    #                       |
|    ##  ##  #       #    #   #  #   #    #   #  #   #               ###     |
|    # ## #  #####   #       #    #  ######  #    #  #              #   #    |
|    #    #  #       #  ###  ######  #    #  ######  #       #   #   ###     |
|    #    #  #       #    #  #    #  #    #  #    #  #        # #   #   #    |
|    #    #  ######   ####   #    #  #    #  #    #  ######    #     ###  r5 |
|                                                                            |
+----------------------------------------------------------------------------+
|                                                                            |
| Copyright (C) 1998 Jason Hutchens                                          |
|                                                                            |
| This program is free software; you can redistribute it and/or modify it    |
| under the terms of the GNU General Public License as published by the Free |
| Software Foundation; either version 2 of the license or (at your option)   |
| any later version.                                                         |
|                                                                            |
| This program is distributed in the hope that it will be useful, but        |
| WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY |
| or FITNESS FOR A PARTICULAR PURPOSE.  See the Gnu Public License for more  |
| details.                                                                   |
|                                                                            |
| You should have received a copy of the GNU General Public License along    |
| with this program; if not, write to the Free Software Foundation, Inc.,    |
| 675 Mass Ave, Cambridge, MA 02139, USA.                                    |
|                                                                            |
+----------------------------------------------------------------------------+

1  INTRODUCTION
---------------

Conversation simulators are computer programs which give the appearance of
conversing with a user in natural language.  Such programs are effective
because they exploit the fact that human beings tend to read much more
meaning into what is said than is actually there; we are fooled into reading
structure into chaos, and we interpret non-sequitur as valid conversation.

MegaHAL differs from conversation simulators such as ELIZA in that it uses
a Markov Model to learn how to hold a conversation.  It is possible to
teach MegaHAL to talk about new topics, and in different languages.

MegaHAL was written by Jason Hutchens
(http://www.amristar.com.au/~hutch/) for the 1998 Loebner contest,
where it placed second.

2  PROGRAM USAGE
----------------

There are two rather complicated ways of starting the program:

* Go to MS-DOS, change to the MEGAHAL directory, and type "MEGAHAL".

* OR, go to Explorer, find the MEGAHAL directory, and double-click on
  "MEGAHAL.EXE".

If you're lucky enough to be using MegaHAL on a machine other than a
PC, then you should also be wise enough to know how to start the program!

There may be a delay as the program either loads in the current brain
file, or trains itself on the training corpus.  After this delay, MegaHAL
will greet you, and when it is done you will be presented with this prompt:

> _

You may now converse with MegaHAL as normal.  Try teaching it your name!

2.1  MEGAHAL COMMANDS
---------------------

Simply type "#help" while using the program to display a help message for
all available commands.  A quick summary is below:

#QUIT   : quits the program and saves MegaHAL's brain
#EXIT   : exits the program *without* saving MegaHAL's brain
#SAVE   : saves the current MegaHAL brain
#DELAY  : toggles MegaHAL's typing delay (off by default)
#SPEECH : toggles MegaHAL's speech (off by default)
#HELP   : displays this message

3  HOLDING A CONVERSATION
-------------------------

To talk to the program, type your message after the prompt.  You may
press <ENTER> to allow your message to span several lines.  To send the
message to MegaHAL, you must press <ENTER> twice.  For example:

Hello there!
> Hello.  My name is Jason<ENTER>
> Hutchens.  What is your<ENTER>
> name?<ENTER>
> <ENTER>
My name is none of your business!

To exit the program, type "#quit".  MegaHAL will save its brain to disk
before returning to DOS.  If you want to quit the program without the
MegaHAL brain being saved first, type "#exit".  To save the brain at any
time, type "#save".  The next time you start the program, this brain will
be loaded so you can begin from where you left off.

4  FILES
--------

You will have noticed several files in the MegaHAL directory.  In this
section I'll explain what they all do:

4.1  MEGAHAL.BRN
----------------

This is MegaHAL's brain.  You mustn't modify it, or look at it.  Actually,
the less said about it the better.  If you delete it, MegaHAL will begin
with no brain.  This is the default situation.  When no brain file is
present, MegaHAL will look for a training file...

4.2  MEGAHAL.TRN
----------------

This is the training file.  It contains lots of sentences for MegaHAL to
learn.  Of course, you may delete the training file if you wish to begin
with a clean slate.  The training file will only be read if no brain file
exists.

MegaHAL reads from this file one line at a time, so a sentence must not
contain any <ENTER> characters, or MegaHAL will only learn half the
sentence!

You may put comments anywhere in the file using the "#" character to
identify them.

4.3  MEGAHAL.DIC
----------------

Whenever MegaHAL saves its brain, it also saves a dictionary containing
all the words it knows (note that spaces and punctuation are also
considered words).   This file isn't used by MegaHAL, it is generated
purely for your benefit.

4.4  MEGAHAL.GRT
----------------

MegaHAL generates replies randomly, but it guarantees that they contain
at least one KEYWORD.  This file contains keywords which will be used
whenever MegaHAL is greeting a new JUDGE.  Typically words such as HELLO
will appear in this file, although you may add any words which you wish
MegaHAL to use in a greeting.  As with all files of this nature, you may
specify only one word per line.

4.5  MEGAHAL.BAN
----------------

This file contains a list of words which can never be used as keywords.
For instance, THE is a common word, and it's presence in the input does
not mean it should be in the output.  Therefore it should appear in this
file.

MegaHAL gets keywords from the input.  So, if you type something such as
"what is the weather like?", MegaHAL should base a reply on the word
WEATHER, not the word THE.  It will do this if the words WHAT, IS, THE and
LIKE appear in this file.

4.6  MEGAHAL.SWP
----------------

This file contains pairs of words.  The leftmost word replaced with the
rightmost word when used as a keyword.  For example, if MY appears in the
input, then YOUR will be used as a keyword.  The file has two words per
line, separated by space.  The rightmost words should not appear in the
file MEGAHAL.BAN, or else they won't be used.

4.7  MEGAHAL.AUX
----------------

This file contains auxiliary keywords.  That is, keywords which can only
be used to generate the output if other keywords appear in it as well.
Most of the words in MEGAHAL.SWP are auxiliary keywords.  For instance,
if you type "What is my name", MegaHAL should use "YOUR" and "NAME" as
keywords, where "YOUR" is auxiliary.

Basically, "YOUR" will only appear in the reply if "NAME" appears, but
"NAME" can appear without "YOUR".  Think about it.  It makes sense.

4.8  MEGAHAL.TXT
----------------

This is the transcript file.  It starts with a short copyright message,
and continues with a complete log of your conversations with the program.
Each interaction is timestamped.

4.9  MEGAHAL.LOG
----------------

This file contains all the error messages generated by MegaHAL.  If
something goes wrong, look in here first.

4.10  PAPER.DOC
---------------

This is a plain ASCII version of a paper I intend to present at a
Human-Computer Communication workshop which is to be held concurrently
with the 1998 Loebner Contest.  It contains some amusing anecdotal
observations of the online MegaHAL, and may shed some light on the
workings of the program if you're a hacker-type trying to decode the
source.

5  TROUBLE-SHOOTING
-------------------

Q: Why does MegaHAL say "I don't know enough to answer you yet!"
A: MegaHAL says this when it was unable to generate a reply.  It was
   probably unable to load the brain file and/or training file, and so
   it has no knowledge of language.  Speak to it for a while.  It should
   start replying soon.

Q: Why does MegaHAL say "I am utterly speechless!"
A: This can occur when MegaHAL has a very tiny brain.  What happens is
   that it generates an empty reply, and so a hardwired sentence is
   displayed.  Again, you should only see it at the beginning of training.

Q: Why does MegaHAL say "I forgot what I was going to say!"
A: This can occur when MegaHAL fails to allocate enough memory for its
   answer.  I will be very surprised indeed if you ever see it.

Q: Why can't I stop the program by breaking it?
A: I trap breaks to avoid silly judge people stopping the program.  To
   exit, just type "#quit" or "#exit" (see the section on commands).

Q: The program died.  What should I do?
A: Tell me about it, especially any error messages you received.  Some
   of these error messages will be in "MEGAHAL.LOG", so send that file
   to me with your bug report.

Q: Hey man, this is freaky!  This program is learning!  Is my computer
   becoming real intelligent, or is there a real person connected to
   this thing?  It's scaring me, man!  This computer is being blasphemous.
   It's possessed by Satan!  Etcetera...
A: You're anthropomorphising.  Go get a dictionary, find out what the word
   means, then make yourself a nice cup of tea and have a quiet lie down.

6  POSTCARD-WARE
----------------

MegaHAL is postcard-ware.  If you enjoy using it, please send me a postcard
from your part of the word.  Mail postcards to the following address:

  Jason Hutchens
  3 Giddens Crt,
  North Lake, WA
  AUSTRALIA 6163

Other correspondence, including bug reports, should be sent by email to:

      davidw@dedasys.com or hutch@ciips.ee.uwa.edu.au (the author of
      the program, but no longer maintaining it)

Thanks muchly!

7  BUGS
-------

Feel free to report any!  Visit the sourceforge project and file them there.

8  PORTING
----------

If you would like to compile MegaHAL for another architecture, please
send have a look at the sourceforge site at
http://www.sourceforge.net/projects/megahal/.

9  CREDITS
----------

* Jason Hutchens
* Dan Agren (Amiga port)
* Paul Baxter (Mac port and extra code)
* Doug Turner (Mac port and extra code)
* Bjorn Karlowsky (OS/2 post)
* Lucas Vergnettes (PPC Linux port)
* Joey Hess (Original Debian maintainer)

+----------------------------------------------------------------------------+
|                                                                            |
|    #    #  ######   ####     ##    #    #    ##    #                       |
|    ##  ##  #       #    #   #  #   #    #   #  #   #               ###     |
|    # ## #  #####   #       #    #  ######  #    #  #              #   #    |
|    #    #  #       #  ###  ######  #    #  ######  #       #   #   ###     |
|    #    #  #       #    #  #    #  #    #  #    #  #        # #   #   #    |
|    #    #  ######   ####   #    #  #    #  #    #  ######    #     ###  r5 |
|                                                                            |
+----------------------------------------------------------------------------+
