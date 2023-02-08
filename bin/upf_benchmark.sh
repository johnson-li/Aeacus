rm /tmp/upf_*

test_sequential() {
  for i in $(seq 100); do
    ~/bin/http3-client https://mobix.aeacus.xuebing.me:4433 2>>/tmp/upf_benchmark_aeacus.log
  done

  for i in $(seq 100); do
    ~/bin/http3-client https://mobix.xuebing.me:4433 2>>/tmp/upf_benchmark_direct.log
  done
}

test_parallel() {
  for concurrency in 10 20 50 80 100 200 300 500; do
    for i in $(seq $concurrency); do
      ~/bin/http3-client https://mobix.aeacus.xuebing.me:4433 2>>/tmp/upf_benchmark_parallel_${concurrency}_aeacus.log &
    done
    sleep 20

    for i in $(seq $concurrency); do
      ~/bin/http3-client https://mobix.xuebing.me:4433 2>>/tmp/upf_benchmark_parallel_${concurrency}_direct.log &
    done
    sleep 20
  done
}

#test_sequential
test_parallel
