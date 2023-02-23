cd ../src

python -m aeacus.fake_client_dns > ../resources/results/handshake_delay_dns.log &
python -m aeacus.fake_client_aeacus > ../resources/results/handshake_delay_aeacus.log &