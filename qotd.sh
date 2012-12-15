#!/bin/bash

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

cd ~nikkybot/bot

touch qotd.txt
qotd=$(grep ^$(date +%Y%m%d) qotd.txt)
if [ -n "$qotd" ]; then
    echo "$qotd" | cut -d ' ' -f 2-
    exit 0
fi

act=$(($RANDOM%5))
if [ $act -eq 0 ]; then
    qotd=$(./random-nikkysim-quote)
else
    qotd=$(echo -e "#exit\n" | megahal -b -p -w 2> /dev/null)
fi

./isRepeatedQOTD.py "$qotd"
if [ $? -eq 1 ]; then
    ./qotd.sh
else
    echo $qotd
    echo -e "$(date +%Y%m%d) $qotd" >> qotd.txt
fi
