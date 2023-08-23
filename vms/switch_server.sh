#!/bin/bash

if [ $# -eq 0 ]
then
    echo "Switch to server 2"
    ssh -F tmp/ssh-config server1 'sudo killall http3-server'
    ssh -F tmp/ssh-config server2 'tmux send-key -t main:4 "cd ~/bin; sudo ./http3-server 192.168.57.14" Enter'
    ssh mobix 'echo 192.168.57.14 > /tmp/server_ip.txt'
else
    echo "Switch to server 1"
    ssh -F tmp/ssh-config server1 'tmux send-key -t main:4 "cd ~/bin; sudo ./http3-server 192.168.57.13" Enter'
    ssh -F tmp/ssh-config server2 'sudo killall http3-server'
    ssh mobix 'echo 192.168.57.13 > /tmp/server_ip.txt'
fi