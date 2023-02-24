#!/bin/bash

while getopts :t flag
do
    case "${flag}" in
        t) test=1;;
    esac
done


cd ../src
if [[ "$test" == "1" ]]; then
  printf "\n===Testing DNS CLoud===\n"
  python -m aeacus.fake_client_dns -s cloud -t3
  printf "\n===Testing Aeacus CLoud===\n"
  python -m aeacus.fake_client_aeacus -s cloud -t3
  printf "\n===Testing DNS Edge===\n"
  python -m aeacus.fake_client_dns -s edge -t3
  printf "\n===Testing Aeacus Edge===\n"
  python -m aeacus.fake_client_aeacus -s edge -t3
else
  echo Running in tmux
  tmux has-session -t main 2>/dev/null
  if [[ $? == 0 ]]; then tmux kill-session -t main; fi
  tmux new-session -ds main
  for i in $(seq 4); do
    tmux new-window -t main:"${i}"
  done
  tmux send-key -t main:0 "conda activate dev; python -m aeacus.fake_client_dns -s cloud > ../resources/results/handshake_delay_cloud_dns.log" Enter
  tmux send-key -t main:1 "conda activate dev; python -m aeacus.fake_client_aeacus -s cloud > ../resources/results/handshake_delay_cloud_aeacus.log" Enter
  tmux send-key -t main:2 "conda activate dev; python -m aeacus.fake_client_dns -s edge > ../resources/results/handshake_delay_edge_dns.log" Enter
  tmux send-key -t main:3 "conda activate dev; python -m aeacus.fake_client_aeacus -s edge > ../resources/results/handshake_delay_edge_aeacus.log" Enter
fi
