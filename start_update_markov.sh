#!/bin/bash

set -e

pickles="nikky-markov.2.pickle nikky-markov.3.pickle nikky-markov.4.pickle nikky-markov.5.pickle"

./update_markov.py
for p in $pickles; do
    chmod 640 $p.new
    mv $p.new $p
done

