
This directory contains the source code.  There isn't really any formal
documentation here.  You may or may not have to poke around and edit things to
make it work/build.  I used the ./build.sh script for building during
development (KTIGCC hasn't been maintained in ages, so no .tpr) to build the
calculator programs and the command-line utility.  This all works on my copy
of Arch Linux.  I know nothing about development on MS Windows, so you're on
your own there.  :-)

The PC utility is just a primitive CLI app that prints the same Mersenne Twister
sayings that the calculator version generates.  It can be useful for searching
for sayings much faster than is possible on the calculator, e.g.:

./nikky 0-123 10000-123 | grep -i -E '(kerm|kermm|kerm martian|christopher) is '

It's very simple and not multithreaded, so if you have multiple CPUs/cores,
fastest speed will be achieved running one process per core, each working on
a different region of sayings numbers.
