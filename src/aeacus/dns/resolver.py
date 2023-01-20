import asyncio
import socket
from asyncio import Future, DatagramProtocol
import time

from dnslib import DNSRecord, DNSError, DNSLabel
from dnslib.dns import QTYPE, EDNS0, CLASS, CNAME, A, NS

CACHE = {}


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


def get_from_cache(key, check_ttl=True):
    ans = CACHE.get(key, None)
    if ans:
        if check_ttl:
            if ans[0] + ans[2] >= time.time():
                return ans
            else:
                CACHE.pop(key)
        else:
            return ans
    return None


def update_cache(record: DNSRecord):
    for r in record.rr:
        data = r.rdata
        if type(data) == CNAME:
            data = data.label
        CACHE[(r.rname, QTYPE.get(r.rtype), CLASS.get(r.rclass))] = (time.time(), data, r.ttl)


async def send_with_retry_async(request, addr, timeout=3, retries=3):
    record = asyncio.get_running_loop().create_future()
    for i in range(retries):
        try:
            await dns_send(*addr, request.pack(), record)
            ans = await asyncio.wait_for(record, timeout)
            reply = DNSRecord.parse(ans)
            if reply.header.id != request.header.id:
                raise DNSError("Reply ID mismatch", request, reply)
            update_cache(reply)
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


async def resolve_authoritative_name_server_async(domain_name, resolver='192.5.6.30'):
    cached = get_from_cache((domain_name, 'NS', 'IN'))
    if cached:
        return cached[1]
    ns_a_request = DNSRecord.question(domain_name, "NS")
    ns_a_request.add_ar(EDNS0(udp_len=1024))
    a: DNSRecord = await send_with_retry_async(ns_a_request, (resolver, 53))
    cached = get_from_cache((domain_name, 'NS', 'IN'))
    if cached:
        return cached[1]
    raise DNSError(f"No DNS NS records found for {domain_name}")


async def resolve_name_recursively_async(domain_name):
    domain_name = DNSLabel(domain_name)
    print(f'Resolve {domain_name} recursively')
    cached = get_from_cache((domain_name, 'A', 'IN'))
    if cached:
        return cached
    cached = get_from_cache((domain_name, 'CNAME', 'IN'))
    if cached:
        return await resolve_name_recursively_async(cached[1])
    ns = await resolve_authoritative_name_server_async(domain_name)
    return await resolve_name_iteratively_async(domain_name, resolver=ns)


async def resolve_name_iteratively_async(domain_name, resolver='127.0.0.53'):
    domain_name = DNSLabel(domain_name)
    print(f'Resolve {domain_name} iteratively, resolver: {resolver}')
    cached = get_from_cache((DNSLabel(domain_name), 'A', 'IN'))
    if cached:
        return cached
    cached = get_from_cache((DNSLabel(domain_name), 'CNAME', 'IN'))
    if cached:
        return await resolve_name_iteratively_async(cached[1], resolver)
    q = DNSRecord.question(domain_name)
    a: DNSRecord = await send_with_retry_async(q, (resolver, 53))
    cached = get_from_cache((DNSLabel(domain_name), 'A', 'IN'))
    if cached:
        return cached
    cached = get_from_cache((DNSLabel(domain_name), 'CNAME', 'IN'))
    if cached:
        return await resolve_name_iteratively_async(cached[1], resolver)
    raise DNSError(f"No DNS A records found for {domain_name}")


def resolve_name_iteratively(domain_name, resolver='8.8.8.8'):
    q = DNSRecord.question(domain_name)
    cached = get_from_cache((domain_name, QTYPE.A, CLASS.IN))
    if cached:
        return cached
    a: DNSRecord = send_with_retry(q, (resolver, 53))
    cached = get_from_cache((domain_name, QTYPE.A, CLASS.IN))
    if cached:
        return cached
    raise DNSError("No DNS A records found")


if __name__ == '__main__':
    a = resolve_name_iteratively("aeacus.xuebing.me")
    print(a)
