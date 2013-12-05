#!/bin/bash
cd ~nikkybot/bot
py=$(cat $(find -name \*.py) | wc -l | cut -d ' ' -f 1)
c=$(cat $(find -name \*.c -or -name \*.h) | wc -l | cut -d ' ' -f 1)
sh=$(cat $(find -name \*.sh) | wc -l | cut -d ' ' -f 1)
all=$(($py + $c + $sh))

echo "Let's see..."
echo "$py lines of Python, $c lines of C, $sh lines of shell scripts"
echo "$all total"

