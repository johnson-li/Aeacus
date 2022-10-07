sudo ovs-vsctl del-br br0
sudo ovs-vsctl add-br br0
sudo ovs-vsctl set bridge br0 other_config:hwaddr=3a:4d:a7:05:2a:45
sudo ovs-vsctl add-port br0 gre0 -- set interface gre0 type=gre options:remote_ip=192.168.56.102
sudo ifconfig br0 10.0.2.15
sudo ip route del default
sudo ip route add default via 10.0.2.14 dev br0
