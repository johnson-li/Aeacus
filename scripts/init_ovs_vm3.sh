sudo ovs-vsctl del-br br0
sudo ovs-vsctl add-br br0
sudo ovs-vsctl add-port br0 gre0 -- set interface gre0 type=gre options:remote_ip=192.168.56.102
sudo ifconfig br0 192.168.57.5

sudo ovs-ofctl del-flows br0
sudo ovs-ofctl add-flow br0 in_port=gre0,actions=br0
sudo ovs-ofctl add-flow br0 in_port=br0,actions=gre0
