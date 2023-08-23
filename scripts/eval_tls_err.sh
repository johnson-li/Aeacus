#!/bin/bash

path=~/Workspace/Aeacus/resources/results/eval_tls_err
mkdir -p $path

for ip in `cat ~/Workspace/Aeacus/resources/results/quic_support2_ip.txt`
do
    log=$path/$ip.log
    for i in seq 1 30
    do
        res=`find $path -name $ip.log -size +1k`
        if [[ -z $res ]]; then
            echo "Testing $ip"
            ~/Workspace/Aeacus/bin/http3-client -u https://xuebing.online -s $ip -v > $log 2>&1
        else
            echo "Skip $ip"
            break
        fi
    done
done