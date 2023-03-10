tmux has-session -t main 2>/dev/null
if [[ $? == 0 ]]; then tmux kill-session -t main; fi
tmux new-session -ds main
for i in $(seq 4); do
  tmux new-window -t main:${i}
done

DOMAIN_COUNT=484
tmux send-key -t main:0 "ping 192.168.57.1" Enter
tmux send-key -t main:1 "ping 192.168.58.1" Enter

if [[ $(hostname) == 'easdf' ]]; then
  tmux send-key -t main:3 "cd ~/python; python3 -m aeacus.dns_legacy_patched" Enter
#  tmux send-key -t main:4 "cd ~/python; sudo python3.11 -m aeacus.dns_aeacus_aio --nic-ingress br0 --nic-egress br0" Enter
  tmux send-key -t main:4 "cd ~/bin; sudo ./quic-resolver" Enter
elif [[ $(hostname) == 'server1' || $(hostname) == 'server2' ]]; then
  tmux send-key -t main:4 "cd ~/python; python3 -m aeacus.dummy_server --certificate ../resources/aeacus_secrets/fullchain.pem --private-key ../resources/aeacus_secrets/privkey.pem" Enter
elif [[ $(hostname) == 'upf' ]]; then
  tmux send-key -t main:2 "sudo ip route del default; sudo ip route add default via 10.0.10.12 dev br0" Enter
#  tmux send-key -t main:4 "~/bin/upf_eval.sh" Enter
elif [[ $(hostname) == 'asdf' ]]; then
  echo 'Nothing to do'
fi

echo "Finish setup $(hostname)"
