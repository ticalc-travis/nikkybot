#!/bin/bash

set -e

./updatevocab.py
tigcc -pack nikkyppg -Wall -O3 nikky.c generate.c ui.c vocab.c
gcc -DCLI_PC_BUILD -O3 nikky-cli.c generate.c vocab.c -o nikky
