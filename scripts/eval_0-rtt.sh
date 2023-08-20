#!/bin/bash

readarray -t domains < ~/Workspace/Aeacus/resources/results/quiche_support.txt
mkdir -p ~/Workspace/Aeacus/resources/results/eval_0-rtt

for domain in "${!domains[@]}"
do
    echo Evaluating ${domain}
    ts=$(date +%s%3N)
    ~/Workspace/Aeacus/bin/http3-client -u https://${domain} -l 127.0.0.1:8053 2> ~/Workspace/Aeacus/resources/results/eval_0-rtt/${ts}_${domain}_dns.txt &
    sleep .3
done
