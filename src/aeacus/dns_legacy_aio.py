import argparse
import asyncio
import socket
import struct
import time

import traceback
from asyncio import DatagramProtocol, Future

from dnslib import DNSRecord, DNSError, QTYPE, RCODE, RR, EDNS0, CLASS, DNSQuestion, EDNSOption, A, CNAME

from aeacus.dns.resolver import resolve_name_recursively_async, resolve_name_iteratively_async, get_ns_from_soa, \
    resolve_ns_async, send_with_retry_async, CACHE

PCI_EDNS_OPTION_CODE = 65001
PCI_EDNS_OPTION_DATA_FMT = '!H'
PCI = 10101


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
    def __init__(self, ns='1.1.1.1'):
        self.udplen = 1024
        self.system_resolver = (ns, 53)
        self.timeout = 3
        self.max_retries = 3

    def try_fail_early(self, request):
        reply = request.reply(ra=1, aa=0)
        opt_count = count_edns_opt_pseudo_rrs(request)
        if opt_count > 1:
            reply.header.rcode = RCODE.FORMERR
            reply.add_ar(EDNS0(udp_len=self.udplen))
            return reply
        if opt_count == 1:
            if get_edns_version(request) != 0:
                reply.add_ar(EDNS0(ext_rcode=1, udp_len=self.udplen))
                return reply
            reply.add_ar(EDNS0(udp_len=self.udplen))
        if request.q.qclass != CLASS.IN:
            reply.header.rcode = RCODE.REFUSED
            return reply

    def get_start_of_authority(self, qname):
        soa_request = DNSRecord.question(qname, "SOA")
        soa_request.add_ar(EDNS0(udp_len=self.udplen))
        try:
            soa_reply = send_with_retry(
                soa_request, self.system_resolver, self.timeout, self.max_retries)
            check_rcode(soa_reply)
            return soa_reply
        except DNSError as exc:
            raise Exception(f"Querying type SOA record for '{qname}'") from exc

    def resolve_authoritative_nameserver(self, soa_rr):
        ns_a_request = DNSRecord.question(soa_rr, "NS")
        ns_a_request.add_ar(EDNS0(udp_len=self.udplen))
        try:
            ns_a_reply = send_with_retry(
                ns_a_request, self.system_resolver, self.timeout, self.max_retries)
            check_rcode(ns_a_reply)
        except DNSError as exc:
            raise Exception(f"Querying type A record for the authoritative nameserver '{soa_rr.rdata.mname}'") from exc
        for rr in ns_a_reply.rr:
            if check_rr_matches_question(rr, ns_a_request.q):
                return str(rr.rdata)
        raise Exception(f"No A records found for the authoritative nameserver '{soa_rr.rdata.mname}'")

    async def query_authoritative_nameserver(self, auth_request, ns_ip):
        try:
            return await send_with_retry(
                auth_request, (ns_ip, 53), self.timeout, self.max_retries)
        except DNSError as exc:
            raise Exception(f"Querying the authoritative nameserver for '{auth_request.q}'") from exc

    async def resolve(self, request):
        domain_name = request.q.qname
        reply = request.reply(ra=1, aa=0)
        edns_options = [EDNSOption(PCI_EDNS_OPTION_CODE, struct.pack(PCI_EDNS_OPTION_DATA_FMT, PCI))]
        req = DNSRecord.question(request.q.qname, qtype=QTYPE[request.q.qtype])
        req.add_ar(EDNS0(udp_len=self.udplen, opts=edns_options))
        try:
            resolver = self.system_resolver[0]
            if resolver:
                await resolve_name_iteratively_async(domain_name, resolver)
            else:
                await resolve_name_recursively_async(domain_name)
            cname = domain_name
            while cname:
                record = CACHE.get((cname, 'A', 'IN'), None)
                if record:
                    reply.add_answer(*RR.fromZone(f"{cname} {record[2]} A {record[1]}"))
                    # reply.add_answer([RR(cname, QTYPE.A, CLASS.IN, record[2], A(record[1]))])
                    break
                record = CACHE.get((cname, 'CNAME', 'IN'), None)
                if record:
                    reply.add_answer(*RR.fromZone(f"{cname} {record[2]} CNAME {record[1]}"))
                    # reply.add_answer([RR(cname, QTYPE.CNAME, CLASS.IN, record[2], CNAME(record[1]))])
                    cname = record[1]
                else:
                    break
        except Exception as exc:
            traceback.print_exc()
            # print("Failed to resolve:", exc)
            reply.header.rcode = RCODE.NXDOMAIN
            # if edns_in_request:
            #     reply.add_ar(EDNS0(udp_len=self.udplen))
        # print(f'Ts: {datetime.now().strftime("%Y/%m/%d-%H:%M:%S")}\nReply: {reply}', flush=True)
        return reply


class UdpServerProtocol(DatagramProtocol):
    def __init__(self, resolver):
        self.resolver: BaseResolver = resolver
        self.transport = None

    async def get_reply(self, data):
        ts = time.time()
        request = DNSRecord.parse(data)
        reply = await self.resolver.resolve(request)
        print(f'It takes {(time.time() - ts) * 1000:.01f} ms to resolve {request.q.qname}')
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
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=str, default=8053)
    parser.add_argument('-n', '--ns', type=str, default=None)
    args = parser.parse_args()
    resolver = BaseResolver(args.ns)
    loop = asyncio.get_running_loop()
    await loop.create_datagram_endpoint(
        lambda: UdpServerProtocol(resolver),
        local_addr=('0.0.0.0', args.port))
    await asyncio.sleep(10000000)


if __name__ == "__main__":
    asyncio.run(main())
