echo '' >benchmark_dns.log

cd ../src
conda activate dev

for i in $(seq 1); do
  python -m aeacus.dummy_client https://localhost:8443
done
