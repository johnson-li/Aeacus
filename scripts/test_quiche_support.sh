#!/bin/bash

path=~/Workspace/Aeacus/resources/results/quiche_test
mkdir -p $path

for domain in `cat ~/Workspace/Aeacus/resources/alexa_top_500.txt`
do
    log=$path/$domain.log
    if [[ -f $log ]]; then
        continue
    fi
    ~/Workspace/Aeacus/bin/http3-client https://$domain > $log 2>&1
done
