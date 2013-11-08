#!/bin/bash

set -e

if [ -z $1 ]; then
    echo "Usage: $0 order"
    exit 1
fi

rm -f markov/new.nikky-markov.$1.{wf,wb,cf,cb} markov/__db.new.*-markov.*
./update_markov.py $1
cd markov
for s in wf wb cf cb; do
    chmod 640 new.nikky-markov.$1.$s
    mv new.nikky-markov.$1.$s nikky-markov.$1.$s
done

