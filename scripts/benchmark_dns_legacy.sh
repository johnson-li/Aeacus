echo '' >benchmark_dns.log

for i in $(seq 1000); do
  dig mobix.xuebing.me @localhost -p 8053 >> benchmark_dns.log &
done
