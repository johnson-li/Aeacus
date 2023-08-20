import asyncio
import socket
import struct
from asyncio import Future, DatagramProtocol
import time

from dnslib import DNSRecord, DNSError, DNSLabel
from dnslib.dns import QTYPE, EDNS0, CLASS, CNAME, A, NS, DNSQuestion, SOA, EDNSOption

PCI_EDNS_OPTION_CODE = 65001
PCI_EDNS_OPTION_DATA_FMT = '!H'
PCI = 10101
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
    return await loop.create_datagram_endpoint(lambda: DnsSendProtocol(request, future), remote_addr=(address, port))


def get_from_cache(key, check_ttl=True):
    ans = CACHE.get(key, None)
    if ans:
        if check_ttl:
            if ans[0] + max(ans[2], 300) >= time.time():
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
        # print(f'[{time.time()}] Update cache, {(r.rname, QTYPE.get(r.rtype), CLASS.get(r.rclass))} : {(data, r.ttl)}')
        CACHE[(r.rname, QTYPE.get(r.rtype), CLASS.get(r.rclass))] = (time.time(), data, r.ttl)


async def send_with_retry_async(request, addr, timeout=3, retries=3):
    record = asyncio.get_running_loop().create_future()
    for i in range(retries):
        try:
            print(f'Send dns query to {addr}')
            transport, protocol = await dns_send(*addr, request.pack(), record)
            ans = await asyncio.wait_for(record, timeout)
            transport.close()
            reply = DNSRecord.parse(ans)
            if reply.header.id != request.header.id:
                raise DNSError("Reply ID mismatch", request, reply)
            update_cache(reply)
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
                return cc
    return None


async def resolve_ns_async(domain_name: DNSLabel, ns_level=0):
    print(f'[{time.time()}] Resolve NS for {domain_name}, ns_level: {ns_level}')
    ns = get_ns_from_soa(domain_name)
    if ns and ns[1] != domain_name:
        return ns
    cached = get_from_cache((domain_name, 'NS', 'IN'))
    if cached:
        return cached
    ns_request = DNSRecord.question(domain_name, "NS")
    ns_request.add_ar(EDNS0(udp_len=1024))
    for i in range(0, len(domain_name.label) - ns_level + 1):
        if i == len(domain_name.label):
            update_cache(await send_with_retry_async(ns_request, (DNS_ROOT_LIST['l.root-servers.net.'], 53)))
            return await resolve_ns_async(domain_name, ns_level + 1)
        else:
            cached = get_from_cache((DNSLabel(domain_name.label[i:]), 'NS', 'IN'))
            if cached:
                ns_ip = await resolve_name_recursively_async(cached[1])
                if ns_ip:
                    update_cache(await send_with_retry_async(ns_request, (ns_ip[1], 53)))
                    return await resolve_ns_async(domain_name, ns_level + 1)
    return None


async def resolve_name_recursively_async(domain_name):
    print(f'[{time.time()}] Resolve {domain_name} recursively')
    domain_name = DNSLabel(domain_name)
    cached = get_from_cache((domain_name, 'A', 'IN'))
    if cached:
        return cached
    cached = get_from_cache((domain_name, 'CNAME', 'IN'))
    if cached:
        return await resolve_name_recursively_async(cached[1])
    ns = await resolve_ns_async(domain_name)
    if ns:
        ns = await resolve_name_recursively_async(ns[1])
        a_request = DNSRecord.question(domain_name, "A")
        # edns_options = [EDNSOption(PCI_EDNS_OPTION_CODE, struct.pack(PCI_EDNS_OPTION_DATA_FMT, PCI))]
        # a_request.add_ar(EDNS0(opts=edns_options))
        a_request.add_ar(EDNS0(udp_len=1024))
        ans = await send_with_retry_async(a_request, (ns[1], 53))
        update_cache(ans)
    cached = get_from_cache((domain_name, 'A', 'IN'))
    if cached:
        return cached
    cached = get_from_cache((domain_name, 'CNAME', 'IN'))
    if cached:
        return await resolve_name_recursively_async(cached[1])
    raise Exception(f'Failed to resolve {domain_name}')


async def resolve_name_iteratively_async(domain_name, resolver):
    print(f'[{time.time()}] Resolve {domain_name} iteratively from {resolver}')
    domain_name = DNSLabel(domain_name)
    cached = get_from_cache((DNSLabel(domain_name), 'A', 'IN'))
    if cached:
        return cached
    cached = get_from_cache((DNSLabel(domain_name), 'CNAME', 'IN'))
    if cached:
        return await resolve_name_iteratively_async(cached[1], resolver)
    q = DNSRecord.question(domain_name, 'A')
    edns_options = [EDNSOption(PCI_EDNS_OPTION_CODE, struct.pack(PCI_EDNS_OPTION_DATA_FMT, PCI))]
    q.add_ar(EDNS0(opts=edns_options))
    q.add_ar(EDNS0(udp_len=1024))
    ans = await send_with_retry_async(q, (resolver, 53))
    update_cache(ans)
    cached = get_from_cache((DNSLabel(domain_name), 'A', 'IN'))
    if cached:
        return cached
    cached = get_from_cache((DNSLabel(domain_name), 'CNAME', 'IN'))
    if cached:
        return await resolve_name_iteratively_async(cached[1], resolver)
    raise DNSError(f"No DNS A records found for {domain_name}")
