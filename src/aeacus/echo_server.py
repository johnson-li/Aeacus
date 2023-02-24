import asyncio
from asyncio import DatagramProtocol

UDP_PORT = 8085


class UdpServerProtocol(DatagramProtocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        self.transport.sendto(data, addr)


async def main():
    loop = asyncio.get_running_loop()
    await loop.create_datagram_endpoint(
        lambda: UdpServerProtocol(),
        local_addr=('0.0.0.0', UDP_PORT))
    await asyncio.sleep(10000000)


if __name__ == '__main__':
    asyncio.run(main())
