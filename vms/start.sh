#!/bin/bash

# This file should be executed after `vagrant provision`
# It exits because some provision tasks are not easy to be handled by ansible

mkdir -p tmp
vagrant ssh-config >tmp/ssh-config

for host in 'upf' 'easdf' 'server1' 'server2'; do
  echo Setup aioquic in $host
  rsync -e 'ssh -F tmp/ssh-config' -r ../submodules/aioquic $host:~/
  if [[ $host == 'easdf' ]]; then
      ssh -F tmp/ssh-config $host 'cd aioquic; sudo python3.11 setup.py install > /dev/null'
    else
      ssh -F tmp/ssh-config $host 'cd aioquic; sudo python3 setup.py install > /dev/null'
  fi
done

for host in 'upf' 'server1' 'server2' 'easdf'; do
  echo Setup resource files in $host
  rsync -e 'ssh -F tmp/ssh-config' -r ../resources $host:~/
done

for host in 'asdf' 'server1' 'server2' 'easdf' 'upf'; do
  echo Setup project files in $host
  rsync -e 'ssh -F tmp/ssh-config' -r ../src/aeacus $host:~/python
  rsync -e 'ssh -F tmp/ssh-config' -r ../scripts/run.sh $host:~/
  ssh -F tmp/ssh-config $host 'chmod +x run.sh; ./run.sh'
done
