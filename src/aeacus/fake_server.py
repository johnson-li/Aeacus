import asyncio
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
        uuid = data[:data.find('!')]
        print(f'New client: {addr}, uuid: {uuid}')
        PEERS.clear()
        PEERS[uuid] = (self.transport, addr)
        self.transport.sendto('0'.encode(), addr)


class DnsServerProtocol(DatagramProtocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        dns_data = DNSRecord.parse(data)
        uuid = dns_data.q.qname.label[0].decode()
        trans, peer = PEERS[uuid]
        print(f'Reply to client: {peer} ({uuid})')
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
    await asyncio.sleep(10000)


if __name__ == '__main__':
    asyncio.run(main())
