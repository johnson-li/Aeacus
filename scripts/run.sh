tmux has-session -t main 2>/dev/null
if [[ $? == 0 ]]; then tmux kill-session -t main; fi
tmux new-session -ds main
for i in $(seq 6); do
  tmux new-window -t main:${i}
done

# tmux send-key -t main:0 "ping 192.168.57.1" Enter
# tmux send-key -t main:1 "ping 192.168.58.1" Enter

if [[ $(hostname) == 'easdf' ]]; then
  tmux send-key -t main:3 "cd ~/python; python3 -m aeacus.dns_legacy_aio -p 8053" Enter
  tmux send-key -t main:4 "cd ~/python; python3 -m aeacus.dns_legacy_aio -p 8054" Enter
  tmux send-key -t main:5 "cd ~/bin; sudo ./quic-resolver" Enter
elif [[ $(hostname) == 'server1' ]]; then
  tmux send-key -t main:4 "cd ~/bin; sudo ./http3-server 192.168.57.13" Enter
elif [[ $(hostname) == 'server2' ]]; then
  tmux send-key -t main:4 "cd ~/bin; sudo ./http3-server 192.168.57.14" Enter
elif [[ $(hostname) == 'upf' ]]; then
  echo 'Nothing to do'
  # tmux send-key -t main:2 "sudo ip route del default; sudo ip route add default via 10.0.10.12 dev br0" Enter
#  tmux send-key -t main:4 "~/bin/upf_eval.sh" Enter
elif [[ $(hostname) == 'asdf' ]]; then
  echo 'Nothing to do'
fi

echo "Finish setup $(hostname)"
