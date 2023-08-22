#!/bin/bash

# This file should be executed after `vagrant provision`
# It exits because some provision tasks are not easy to be handled by ansible

~/Workspace/Aeacus/scripts/build_quiche.sh

mkdir -p tmp
vagrant ssh-config >tmp/ssh-config

echo Path host file in UPF
ssh -F tmp/ssh-config upf 'lines=`wc -l < /etc/hosts`; if [[ "$lines" -lt "100" ]]; then for i in `seq 484`; do for j in edge cloud; do echo 192.168.58.13 $i.$j.aeacus| sudo tee -a /etc/hosts; done; done; fi'

# for host in 'upf' 'easdf'; do
#   echo Setup quiche in $host
#   rsync -e 'ssh -F tmp/ssh-config' -L -r ../bin $host:~/
# done

# for host in 'easdf'; do
#   echo Setup aioquic in $host
#   rsync -e 'ssh -F tmp/ssh-config' -r ../submodules/aioquic $host:~/
#   if [[ $host == 'easdf' ]]; then
#       ssh -F tmp/ssh-config $host 'cd aioquic; sudo python3.11 setup.py install > /dev/null'
#     else
#       ssh -F tmp/ssh-config $host 'cd aioquic; sudo python3 setup.py install > /dev/null'
#   fi
# done

# for host in 'upf' 'easdf'; do
#   echo Setup resource files in $host
#   rsync -e 'ssh -F tmp/ssh-config' -r ../resources $host:~/
# done

rsync -e 'ssh -F tmp/ssh-config' ../resources/results/quic_support.txt ue:~/
rsync -e 'ssh -F tmp/ssh-config' ../scripts/eval_0-rtt.sh ue:~/

for host in 'easdf' 'ue'; do
  echo Setup project files in $host
  rsync -e 'ssh -F tmp/ssh-config' -r ../src/aeacus $host:~/python
  rsync -e 'ssh -F tmp/ssh-config' -r ../scripts/run.sh $host:~/
  rsync -e 'ssh -F tmp/ssh-config' -L -r ../bin $host:~/
  ssh -F tmp/ssh-config $host 'chmod +x run.sh; ./run.sh'
done
