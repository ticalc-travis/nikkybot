#!/bin/bash
logfile=~nikkybot/bot/nikkybot.log

cd ~nikkybot/bot
echo -e "\n\nStarting $(date)" >> $logfile
PYTHONUNBUFFERED=1 ./nikkybot.py |& tee -a $logfile
