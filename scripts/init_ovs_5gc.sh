sudo ovs-vsctl del-br br0
sudo ovs-vsctl add-br br0

sudo ovs-vsctl set bridge br0 other_config:hwaddr=3a:4d:a7:05:2a:45
sudo ovs-vsctl add-port br0 gre0 -- set interface gre0 type=vxlan options:remote_ip=192.168.56.102

sudo ovs-ofctl del-flows br0
sudo ovs-ofctl add-flow br0 in_port=gre0,actions=mod_dl_dst:3a:4d:a7:05:2a:45,br0
sudo ovs-ofctl add-flow br0 in_port=br0,actions=gre0

sudo ifconfig br0 10.0.2.15

sudo ip route add default via 10.0.2.2 dev br0
