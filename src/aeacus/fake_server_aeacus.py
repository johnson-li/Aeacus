import asyncio
import time
from asyncio import DatagramProtocol

from dnslib import DNSRecord

PEERS = {}
UDP_PORT = 8083
DNS_PORT = 8053


class UdpServerProtocol(DatagramProtocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        data = data.decode()
        if len(data) == 2 and data[0] == 'C':
            client_id = data[1]
            print(f'New client {client_id} from {addr}')
            PEERS[client_id] = (self.transport, addr)
            self.transport.sendto('0'.encode(), addr)


class DnsServerProtocol(DatagramProtocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        dns_data = DNSRecord.parse(data)
        uuid = dns_data.q.qname.label[0].decode()
        client_id = uuid[0]
        uuid = uuid[1:]
        trans, peer = PEERS[client_id]
        print(f'Reply to client: {peer} ({client_id}), uuid: {uuid}')
        data = (uuid + "!" * (1200 - len(uuid))).encode()
        trans.sendto(data, peer)


async def main():
    loop = asyncio.get_running_loop()
    await loop.create_datagram_endpoint(
        lambda: UdpServerProtocol(),
        local_addr=('0.0.0.0', UDP_PORT))
    await loop.create_datagram_endpoint(
        lambda: DnsServerProtocol(),
        local_addr=('0.0.0.0', DNS_PORT))
    await asyncio.sleep(10000000)


if __name__ == '__main__':
    asyncio.run(main())
