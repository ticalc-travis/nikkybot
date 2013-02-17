#!/bin/bash

set -e

rm -f markov/new.nikky-markov.$1.{wf,wb,cf,cb}
./update_markov.py $1
cd markov
for s in wf wb cf cb; do
    chmod 640 new.nikky-markov.$1.$s
    mv new.nikky-markov.$1.$s nikky-markov.$1.$s
done

