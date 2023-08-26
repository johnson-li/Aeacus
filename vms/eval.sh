
#!/bin/bash

mkdir -p /tmp/benchmark

num=500
mkdir -p /tmp/benchmark/$num
for i in `seq $num`
do
    ~/bin/http3-client -u https://a.ns7.xuebing.online -a 192.168.57.12 > /tmp/benchmark/$num/$i.log 2>&1 &
done
