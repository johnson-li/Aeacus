import asyncio
import socket
import struct
import json
import os

import traceback
from asyncio import DatagramProtocol, Future

from dnslib import DNSRecord, DNSError, QTYPE, RCODE, RR, EDNS0, CLASS, DNSQuestion, EDNSOption, A, CNAME
from dnslib.label import DNSLabel

from aeacus.dns.resolver import resolve_name_recursively_async, resolve_name_iteratively_async, get_ns_from_soa, \
    resolve_ns_async, send_with_retry_async, CACHE
from aeacus import RESULTS_PATH

PCI_EDNS_OPTION_CODE = 65001
PCI_EDNS_OPTION_DATA_FMT = '!H'
PCI = 10101
NS_DELAY = json.load(open(os.path.join(RESULTS_PATH, "dns_ns_delay_values.json")))


def count_edns_opt_pseudo_rrs(dns_record):
    return sum((ar.rtype == QTYPE.OPT for ar in dns_record.ar))


def get_edns_version(dns_record):
    try:
        return next(ar for ar in dns_record.ar if ar.rtype == QTYPE.OPT).edns_ver
    except StopIteration:
        pass


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


async def send_with_retry(request: DNSRecord, address_and_port, timeout, max_retries):
    tries = 0
    record = asyncio.get_running_loop().create_future()
    while tries < max_retries:
        try:
            await dns_send(*address_and_port, request.pack(), record)
            ans = await asyncio.wait_for(record, timeout)
            reply = DNSRecord.parse(ans)
            if reply.header.id != request.header.id:
                raise DNSError("Reply ID mismatch", request, reply)
            return reply
        except (socket.timeout, DNSError):
            tries += 1
        except Exception:
            traceback.print_exc()
    # raise DNSError("Giving up", request, address_and_port, tries)


def check_rcode(reply):
    if reply.header.rcode == RCODE.NOERROR:
        return
    if reply.header.rcode == RCODE.NXDOMAIN:
        raise Exception(reply)
    raise Exception(reply)


def check_rr_matches_question(rr, q):
    return rr.rname == q.qname and rr.rtype == q.qtype and rr.rclass == q.qclass


def match_soa_cname(qname, soa):
    aliases = [qname]
    cname_rrs = []
    for rr in soa.rr:
        if any(check_rr_matches_question(rr, DNSQuestion(alias, QTYPE.CNAME))
               for alias in aliases) and rr.rdata:
            cname_rrs.append(rr)
            aliases.append(rr.rdata.label)
    for rr in soa.rr + soa.auth:
        for alias in aliases:
            if (rr.rclass == CLASS.IN and rr.rtype == QTYPE.SOA
                    and alias.matchSuffix(rr.rname)):
                return rr, alias, cname_rrs
    raise Exception(f"No SOA records matching '{qname}' in reply")


class BaseResolver(object):
    async def resolve(self, request):
        domain_name: DNSLabel = request.q.qname
        reply = request.reply(ra=1, aa=0)
        index, server = domain_name.label[0].decode(), domain_name.label[1].decode()
        delay = 0 if index == 1000 else NS_DELAY[int(index)]
        server = '195.148.127.230' if server == 'edge' else '34.118.22.129'
        print(f'Domain: {domain_name}, delay: {delay}, server: {server}')
        await asyncio.sleep(delay)
        reply.add_answer(*RR.fromZone(f"{domain_name} {60} A {server}"))
        return reply


class UdpServerProtocol(DatagramProtocol):
    def __init__(self, resolver):
        self.resolver: BaseResolver = resolver
        self.transport = None

    async def get_reply(self, data):
        request = DNSRecord.parse(data)
        reply = await self.resolver.resolve(request)
        rdata = reply.pack()
        return rdata

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        asyncio.create_task(self.datagram_received0(data, addr))

    async def datagram_received0(self, data, addr):
        rdata = await self.get_reply(data)
        self.transport.sendto(rdata, addr)


async def main():
    resolver = BaseResolver()
    loop = asyncio.get_running_loop()
    await loop.create_datagram_endpoint(
        lambda: UdpServerProtocol(resolver),
        local_addr=('0.0.0.0', 8053))
    await asyncio.sleep(10000000)


if __name__ == "__main__":
    asyncio.run(main())
