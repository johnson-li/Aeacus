#!/bin/bash

# This file should be executed after `vagrant provision`
# It exits because some provision tasks are not easy to be handled by ansible

mkdir -p tmp
vagrant ssh-config > tmp/ssh-config

for host in 'upf' 'asdf' 'server'; do
  echo Setup aioquic in $host
  rsync -e 'ssh -F tmp/ssh-config' -r ../submodules/aioquic $host:~/
  ssh -F tmp/ssh-config $host 'cd aioquic; sudo python3 setup.py install > /dev/null'
done
