#!/bin/bash

ssh -F tmp/ssh-config server1 'sudo killall http3-server'
ssh -F tmp/ssh-config server2 'tmux send-key -t main:4 "cd ~/bin; sudo ./http3-server 192.168.57.14" Enter'
ssh mobix 'echo 192.168.57.14 > /tmp/server_ip.txt'