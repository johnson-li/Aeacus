target=release

rm dns-client
rm http3-client
rm http3-server
rm quic-proxy
rm quic-resolver

ln -s ../submodules/quiche/target/${target}/examples/dns-client .
ln -s ../submodules/quiche/target/${target}/examples/http3-client .
ln -s ../submodules/quiche/target/${target}/examples/http3-server .
ln -s ../submodules/quiche/target/${target}/examples/quic-proxy .
ln -s ../submodules/quiche/target/${target}/examples/quic-resolver .
