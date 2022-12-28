tmux has-session -t main 2>/dev/null
if [[ $? == 0 ]]; then tmux kill-session -t main; fi
tmux new-session -ds main
for i in $(seq 4); do
  tmux new-window -t main:${i}
done

if [[ $(hostname) == 'easdf' ]]; then
  tmux send-key -t main:0 "cd python; python3 -m aeacus.dns_legacy" Enter
fi
