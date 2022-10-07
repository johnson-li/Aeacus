# Aalto Network Deployment

## Machines

| HostName                          | Management IP Address | VM Subnet IP Address | GRE Tunnel Address | Core Network IP Address | Public IP Address |          
|-----------------------------------|-----------------------|----------------------|--------------------|-------------------------|-------------------|
| VM1 (MEC)                         | 192.168.56.101        | 192.168.57.3         |                    | /                       | /                 |          
| VM2 (UPF extension)               | 192.168.56.102        | 192.168.57.4         | 10.0.10.14         | /                       | /                 |          
| VM3 (EASDF)                       | 192.168.56.103        | 192.168.57.5         | 10.0.10.13         | /                       | /                 |          
| 5GC (with UPF, GRE endpoint)      | 192.168.56.104        | /                    | 10.0.10.15         | 10.128.1.230            | /                 |          
| johnson-HP-Z240-Tower-Workstation | 192.168.56.1          | 192.168.57.1         |                    | 10.128.1.231            | /                 |          
| Base station                      | /                     | /                    |                    | x.x.x.x                 | /                 |          
| MOBIX (Cloud Server)              | 195.148.127.230       | /                    |                    | /                       | 195.148.127.230   |          

## Network Topology

![network topology](https://docs.google.com/drawings/d/e/2PACX-1vTWLVZ1dwrgSdYGV5aKRaoNY28UuppP4N001VHPC3jiPQ3-emHzBzjnaZiuEEQawyVKwRYRM7Erle8j/pub?w=1769&h=709)

## Program Setup

| HostName | Programme                    | Command                                                                                                                                         |
|----------|------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| 5GC      | UPF                          |                                                                                                                                                 |
| 5GC      | QUIC Client                  | ``python -m aeacus.dummy_client https://aeacus.xuebing.me:4433/``                                                                               |
| VM2      |                              |                                                                                                                                                 |
| VM3      | Legacy DNS Server            |                                                                                                                                                 |
| VM3      | DNS Server with Late Binding | ``sudo `which python` -m aeacus.aeacus_dns --nic-egress eno1``                                                                                  |
| VM1      | QUIC Server                  | ``python -m aeacus.dummy_server --certificate ../resources/aeacus_secrets/fullchain.pem --private-key ../resources/aeacus_secrets/privkey.pem`` |
| MOBIX    | QUIC Server                  | ``python -m aeacus.dummy_server --certificate ../resources/aeacus_secrets/fullchain.pem --private-key ../resources/aeacus_secrets/privkey.pem`` |

## OVS Setup

### 5GC

```
Bridge br0
    Port gre0
        Interface gre0
            type: vxlan
            options: {remote_ip="192.168.56.102"}
    Port br0
        Interface br0
            type: internal
            
```

```
cookie=0x0, duration=4241113.360s, table=0, n_packets=4551550, n_bytes=545810184, in_port=gre0 actions=mod_dl_dst:3a:4d:a7:05:2a:45,LOCAL
cookie=0x0, duration=4241113.352s, table=0, n_packets=4345894, n_bytes=419067664, in_port=LOCAL actions=output:gre0
```

### VM2

```
Bridge br0
    Port gre0
        Interface gre0
            type: vxlan
            options: {remote_ip="192.168.56.104"}
    Port enp0s3
        Interface enp0s3
    Port br0
        Interface br0
            type: internal
```

```
cookie=0x0, duration=4240876.337s, table=0, n_packets=4551997, n_bytes=546484292, in_port=enp0s3 actions=output:gre0
cookie=0x0, duration=4240876.327s, table=0, n_packets=4345908, n_bytes=419069220, in_port=gre0 actions=mod_dl_dst:08:00:27:e2:3a:8a,output:enp0s3
```