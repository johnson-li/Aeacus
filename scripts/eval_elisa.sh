#!/bin/bash

readarray -t domains < ~/Workspace/Aeacus/resources/results/quiche_support.txt

while true 
do
    domain=${domains[ $RANDOM % ${#domains[@]} ]}
    echo Evaluating ${domain}
    ts=$(date +%s%3N)
    ~/Workspace/Aeacus/bin/http3-client -u https://${domain} -i 195.148.127.234 -l 195.148.127.234:8053 2> ~/Workspace/Aeacus/resources/results/eval_elisa/${ts}_${domain}_dns.txt &
    ~/Workspace/Aeacus/bin/http3-client -u https://${domain} -a 195.148.127.234 2> ~/Workspace/Aeacus/resources/results/eval_elisa/${ts}_${domain}_aeacus.txt & 
    sleep .3
done
