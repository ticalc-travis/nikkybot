#!/bin/bash

ramuse=$(cat /proc/$1/status | grep VmRSS | cut -d : -f 2)
ramtot=$(cat /proc/meminfo | grep MemTotal | cut -d : -f 2)
swaptot=$(cat /proc/meminfo | grep SwapTotal | cut -d : -f 2)
ramuse=$(($(echo $ramuse | cut -d ' ' -f 1) / 1024))
ramtot=$(($(echo $ramtot | cut -d ' ' -f 1) / 1024))
swaptot=$(($(echo $swaptot | cut -d ' ' -f 1) / 1024))

echo I\'m consuming $ramuse MiB out of $ramtot MiB RAM / $swaptot MiB swap
