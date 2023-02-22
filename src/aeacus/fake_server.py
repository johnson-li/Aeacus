import asyncio
from asyncio import DatagramProtocol


class UdpServerProtocol(DatagramProtocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        pass


class DnsServerProtocol(DatagramProtocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        pass


async def main():
    loop = asyncio.get_running_loop()
    await loop.create_datagram_endpoint(
        lambda: UdpServerProtocol(),
        local_addr=('0.0.0.0', 8083))
    await loop.create_datagram_endpoint(
        lambda: DnsServerProtocol(),
        local_addr=('0.0.0.0', 53))
    await asyncio.sleep(10000)


if __name__ == '__main__':
    asyncio.run(main())
