#!/bin/bash

# This file should be executed after `vagrant provision`
# It exits because some provision tasks are not easy to be handled by ansible

~/Workspace/Aeacus/scripts/build_quiche.sh

mkdir -p tmp
vagrant ssh-config >tmp/ssh-config

rsync -e 'ssh -F tmp/ssh-config' ../resources/results/quic_support.txt ue:~/
rsync -e 'ssh -F tmp/ssh-config' ../scripts/eval_0-rtt.sh ue:~/

for host in 'easdf' 'ue' 'upf' 'server1' 'server2'; do
  echo Setup project files in $host
  rsync -e 'ssh -F tmp/ssh-config' -r ../src/aeacus $host:~/python
  rsync -e 'ssh -F tmp/ssh-config' -r ../scripts/run.sh $host:~/
  rsync -e 'ssh -F tmp/ssh-config' -L -r ../bin $host:~/
  ssh -F tmp/ssh-config $host 'chmod +x run.sh; ./run.sh'
done
