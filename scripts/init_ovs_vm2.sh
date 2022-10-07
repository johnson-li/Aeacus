sudo ovs-vsctl del-br br0
sudo ovs-vsctl add-br br0
sudo ovs-vsctl add-port br0 gre0 -- set interface gre0 type=gre options:remote_ip=192.168.56.104
sudo ovs-vsctl add-port br0 gre1 -- set interface gre1 type=gre options:remote_ip=192.168.56.103

sudo ovs-ofctl del-flows br0
sudo ovs-ofctl add-flow br0 in_port=gre0,ip,nw_proto=17,nw_dst=192.168.57.5/32,actions=gre1
sudo ovs-ofctl add-flow br0 in_port=gre0,actions=br0
sudo ovs-ofctl add-flow br0 in_port=br0,actions=gre0
sudo ovs-ofctl add-flow br0 in_port=gre1,actions=br0

sudo ifconfig br0 10.0.10.14

sudo modprobe iptable_nat
sudo sysctl -w net.ipv4.ip_forward=1

sudo iptables -t nat -A POSTROUTING -o enp0s3 -j MASQUERADE
sudo iptables -A FORWARD -i br0 -j ACCEPT
