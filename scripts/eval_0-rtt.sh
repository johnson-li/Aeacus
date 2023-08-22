#!/bin/bash

readarray -t domains < ~/quic_support.txt
mkdir -p ~/eval_0-rtt

for domain in "${domains[@]}"
do
    for i in `seq 10`
    do
        echo Evaluating ${domain}
        ts=$(date +%s%3N)
        ~/bin/http3-client -u https://${domain} -a 192.168.57.12 -p > ~/eval_0-rtt/${ts}_${domain}_1-rtt.txt 2>&1 
    done
    for i in `seq 10`
    do
        echo Evaluating ${domain}
        ts=$(date +%s%3N)
        ~/bin/http3-client -u https://${domain} -a 192.168.57.12 -pz > ~/eval_0-rtt/${ts}_${domain}_0-rtt.txt 2>&1 
    done
done
