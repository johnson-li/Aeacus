# Aalto Network Deployment

## Machines

| HostName                          | VM Subnet IP Address | Core Network IP Address | Public IP Address |          
|-----------------------------------|----------------------|-------------------------|-------------------|
| VM1 (MEC)                         | 192.168.56.101       | /                       | /                 |          
| VM2 (GRE endpoint)                | 192.168.56.102       | /                       | /                 |          
| VM3                               | 192.168.56.103       | /                       | /                 |          
| 5GC (with UPF, GRE endpoint)      | 192.168.56.104       | 10.128.1.230            | /                 |          
| johnson-HP-Z240-Tower-Workstation | 192.168.56.1         | 10.128.1.231            | /                 |          
| Base station                      | /                    | x.x.x.x                 | /                 |          
| MOBIX (Cloud Server)              | /                    | /                       | 195.148.127.230   |          

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
