import asyncio
import logging
import random
import socket
import traceback
from asyncio import Future, DatagramProtocol
import time

from dnslib import DNSRecord, DNSError, DNSLabel
from dnslib.dns import QTYPE, EDNS0, CLASS, CNAME, A, NS, DNSQuestion, SOA

DNS_ROOT_LIST = {
    'a.root-servers.net.': '198.41.0.4',
    'b.root-servers.net.': '199.9.14.201',
    'c.root-servers.net.': '192.33.4.12',
    'd.root-servers.net.': '199.7.91.13',
    'e.root-servers.net.': '192.203.230.10',
    'f.root-servers.net.': '192.5.5.241',
    'g.root-servers.net.': '192.112.36.4',
    'h.root-servers.net.': '198.97.190.53',
    'i.root-servers.net.': '192.36.148.17',
    'j.root-servers.net.': '192.58.128.30',
    'k.root-servers.net.': '193.0.14.129',
    'l.root-servers.net.': '199.7.83.42',
    'm.root-servers.net.': '202.12.27.33',
}

CACHE = {}
for k, v in DNS_ROOT_LIST.items():
    CACHE[(DNSLabel(k), 'A', 'IN')] = (time.time(), v, 10000000)


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
    address = str(address)
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
    for r in [*reversed(record.auth), *reversed(record.ar), *reversed(record.rr)]:
        data = r.rdata
        if type(data) == CNAME:
            data = data.label
        elif type(data) == NS:
            data = data.label
        elif type(data) == SOA:
            data = data.mname
        elif type(data) == list:
            continue
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


def get_ns_from_soa(domain_name: DNSLabel):
    for i in range(0, len(domain_name.label)):
        cached = get_from_cache((DNSLabel(domain_name.label[i:]), 'SOA', 'IN'))
        if cached:
            cc = get_from_cache((DNSLabel(domain_name.label[i:]), 'NS', 'IN'))
            if cc:
                return cc[1]
            return cached[1]
    return None


async def resolve_ns_async(domain_name: DNSLabel, ns_level=0):
    ns = get_ns_from_soa(domain_name)
    if ns and ns != domain_name:
        print(f'[Cache] {domain_name} has the SOA {ns}')
        return await resolve_name_recursively_async(ns)
    ns_request = DNSRecord.question(domain_name, "NS")
    ns_request.add_ar(EDNS0(udp_len=1024))
    for i in range(1, len(domain_name.label) - ns_level + 1):
        if i == len(domain_name.label):
            print(f'Query NS of {domain_name} from DNS root')
            update_cache(await send_with_retry_async(ns_request, (DNS_ROOT_LIST['l.root-servers.net.'], 53)))
            return await resolve_ns_async(domain_name, ns_level + 1)
        else:
            cached = get_from_cache((DNSLabel(domain_name.label[i:]), 'NS', 'IN'))
            if cached:
                print(f'[Cache] NS of {DNSLabel(domain_name.label[i:])} is {cached[1]}')
                ns_ip = await resolve_name_recursively_async(cached[1])
                if ns_ip:
                    print(f'Query NS of {domain_name} from {ns_ip[1]}')
                    update_cache(await send_with_retry_async(ns_request, (ns_ip[1], 53)))
                    return await resolve_ns_async(domain_name, ns_level + 1)
    return None


async def resolve_name_recursively_async(domain_name):
    domain_name = DNSLabel(domain_name)
    cached = get_from_cache((domain_name, 'A', 'IN'))
    if cached:
        print(f'[Cache] {domain_name} has the IP {cached[1]}')
        return cached
    print(f'Resolve A of {domain_name} recursively')
    cached = get_from_cache((domain_name, 'CNAME', 'IN'))
    if cached:
        return await resolve_name_recursively_async(cached[1])
    ns = await resolve_ns_async(domain_name)
    if ns:
        a_request = DNSRecord.question(domain_name, "A")
        a_request.add_ar(EDNS0(udp_len=1024))
        print(f'Query A of {domain_name} from {ns[1]}')
        update_cache(await send_with_retry_async(a_request, (ns[1], 53)))
    cached = get_from_cache((domain_name, 'A', 'IN'))
    if cached:
        print(f'[Cache] {domain_name} has the IP {cached[1]}')
        return cached
    raise Exception(f'Failed to resolve {domain_name}')


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
    print(f'Query A of {domain_name} from {resolver}')
    update_cache(await send_with_retry_async(q, (resolver, 53)))
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
