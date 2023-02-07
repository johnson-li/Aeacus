test_sequential() {
  for i in $(seq 100); do
    ~/bin/http3-client https://mobix.aeacus.xuebing.me:4433 2>>/tmp/upf_benchmark_aeacus.log
  done

  for i in $(seq 100); do
    ~/bin/http3-client https://mobix.xuebing.me:4433 2>>/tmp/upf_benchmark_direct.log
  done
}

concurrency=100
test_parallel() {
  for i in $(seq $concurrency); do
    ~/bin/http3-client https://mobix.aeacus.xuebing.me:4433 2>>/tmp/upf_benchmark_parallel_aeacus.log &
  done

  for i in $(seq $concurrency); do
    ~/bin/http3-client https://mobix.xuebing.me:4433 2>>/tmp/upf_benchmark_parallel_direct.log &
  done
}

test_sequential
#test_parallel
