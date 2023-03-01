rm /tmp/upf_eval.log
cd ~/python

function run0() {
  for server in cloud edge; do
    domain=$1.${server}.aeacus
    domain_hit=1000.${server}.aeacus

    if [[ $server == "cloud" ]]; then
      ip=34.118.22.129
    else
      ip=195.148.127.230
    fi

    {
      echo Sample domain name: "$domain", ip: $ip
      echo Evaluate DNS
      echo miss: `dig "$domain" @195.148.127.230 -p 8053 | grep 'Query time'`
      echo hit: `dig "$domain_hit" @195.148.127.230 -p 8053 | grep 'Query time'`
      ~/bin/http3-client https://${ip}:4433 2>&1 | grep handshake
      echo Evaluate Aeacus with cache hit
      ~/bin/http3-client https://${domain_hit}:4433 2>&1 | grep handshake
      echo Evaluate Aeacus with cache loss
      ~/bin/http3-client https://"${domain}":4433 2>&1 | grep handshake
    }
  done
}

function run1() {
  for i in $(seq 10); do
    export index=$((RANDOM % 400))
    for j in $(seq 5); do
      run0 ${index} >> /tmp/upf_eval.log
    done
  done
}

function run2() {
  rounds=200
  for i in `seq $rounds`; do
    echo Round "$i/$rounds"
    rtt=$(python3 -m aeacus.sample_ran_rtt)
    echo Sample RTT: "$rtt" >>/tmp/upf_eval.log
    sudo tc qdisc del dev br0 root netem 2>/dev/null
    sudo tc qdisc add dev br0 root netem delay "$rtt"ms
    for j in $(seq 3); do
      run0 1 >> /dev/null
    done
    run1
  done
}

run2
