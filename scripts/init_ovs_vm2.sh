sudo ovs-vsctl del-br br0
sudo ovs-vsctl add-br br0

# sudo ovs-vsctl set bridge br0 other_config:hwaddr=3a:4d:a7:05:2a:45
# sudo ovs-vsctl add-port br0 vlan -- set Interface vlan type=internal
sudo ovs-vsctl add-port br0 enp0s3
sudo ovs-vsctl add-port br0 gre0 -- set interface gre0 type=vxlan options:remote_ip=192.168.56.104


sudo ovs-ofctl del-flows br0
sudo ovs-ofctl add-flow br0 in_port=enp0s3,actions=gre0
sudo ovs-ofctl add-flow br0 in_port=gre0,actions=mod_dl_dst:08:00:27:e2:3a:8a,enp0s3

sudo ifconfig enp0s3 up
sudo ifconfig gre0 up
sudo ifconfig br0 10.0.2.15
# sudo ip route del default
sudo ip route add default via 10.0.2.2 dev br0
