import asyncio
import socket
from asyncio import Future, DatagramProtocol

from dnslib import DNSRecord, DNSError
from dnslib.dns import QTYPE


class DnsSendProtocol(DatagramProtocol):
    def __init__(self, request, future):
        self.future: Future = future
        self.message = request
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        self.transport.sendto(self.message)

    def datagram_received(self, data, addr):
        if not self.future.done():
            self.future.set_result(data)


async def dns_send(address, port, request: DNSRecord, future):
    loop = asyncio.get_running_loop()
    await loop.create_datagram_endpoint(lambda: DnsSendProtocol(request, future), remote_addr=(address, port))


async def send_with_retry_async(request, addr, timeout=3, retries=3):
    record = asyncio.get_running_loop().create_future()
    for i in range(retries):
        try:
            await dns_send(*addr, request.pack(), record)
            ans = await asyncio.wait_for(record, timeout)
            reply = DNSRecord.parse(ans)
            if reply.header.id != request.header.id:
                raise DNSError("Reply ID mismatch", request, reply)
            return reply
        except (socket.timeout, DNSError) as e:
            print(e)
    raise DNSError("All retries failed")


def send_with_retry(request, addr, timeout=3, retries=3):
    for i in range(retries):
        try:
            reply = DNSRecord.parse(request.send(*addr, timeout=timeout))
            if reply.header.id != request.header.id:
                raise DNSError("Reply ID mismatch", request, reply)
            return reply
        except (socket.timeout, DNSError) as e:
            print(e)
    raise DNSError("All retries failed")


async def resolve_name_async(domain_name):
    q = DNSRecord.question(domain_name)
    a: DNSRecord = await send_with_retry_async(q, ("8.8.8.8", 53))
    ans = []
    for r in a.rr:
        if r.rtype == QTYPE.A:
            ans.append(str(r.rdata))
    if ans:
        return ans
    raise DNSError("No DNS A records found")


def resolve_name(domain_name):
    q = DNSRecord.question(domain_name)
    a: DNSRecord = send_with_retry(q, ("8.8.8.8", 53))
    ans = []
    for r in a.rr:
        if r.rtype == QTYPE.A:
            ans.append(str(r.rdata))
    if ans:
        return ans
    raise DNSError("No DNS A records found")


if __name__ == '__main__':
    a = resolve_name("aeacus.xuebing.me")
    print(a)
