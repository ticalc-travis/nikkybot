#!/bin/bash
pytev=$(cat ~nikkybot/bot/*.py | wc -l | cut -d ' ' -f 1)
pyall=$(($pytev + 10125))
ctev=4516
call=$((4358+4516))
shtev=$(cat ~nikkybot/bot/*.sh | wc -l | cut -d ' ' -f 1)
shall=$shtev
all=$(($pyall + $call + $shall))

echo "Let's see..."
echo "$pyall lines of Python, $call lines of C, $shtev lines of shell scripts"
echo "tev only wrote $(echo "($pytev + $ctev + $shtev)*100 / $all" | bc)% of all that, though"

