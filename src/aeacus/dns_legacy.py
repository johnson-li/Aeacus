import socket
import struct
import threading

import socketserver
from datetime import datetime

from dnslib import DNSRecord, DNSError, QTYPE, RCODE, RR, EDNS0, CLASS, DNSQuestion, EDNSOption

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


def send_with_retry(request, address_and_port, timeout, max_retries):
    tries = 0
    while tries < max_retries + 1:
        try:
            reply = DNSRecord.parse(request.send(*address_and_port, timeout=timeout))
            if reply.header.id != request.header.id:
                raise DNSError("Reply ID mismatch", request, reply)
            return reply
        except (socket.timeout, DNSError):
            tries += 1
    raise DNSError("Giving up", request, address_and_port, tries)


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
    def __init__(self):
        self.udplen = 1024
        # self.system_resolver = ("127.0.0.53", 53)
        self.system_resolver = ("1.1.1.1", 53)
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

    def query_authoritative_nameserver(self, auth_request, ns_ip):
        try:
            return send_with_retry(
                auth_request, (ns_ip, 53), self.timeout, self.max_retries)
        except DNSError as exc:
            raise Exception(f"Querying the authoritative nameserver for '{auth_request.q}'") from exc

    def resolve(self, request, handler):
        reply = self.try_fail_early(request)
        if reply:
            return reply
        edns_in_request = (get_edns_version(request) is not None)
        reply = request.reply(ra=1, aa=0)
        try:
            # soa = self.get_start_of_authority(request.q.qname)
            # soa_rr, cname, cname_rrs = match_soa_cname(request.q.qname, soa)
            # ns_ip = self.resolve_authoritative_nameserver(request.q.qname)
            ns_ip = self.system_resolver[0]
            edns_options = [EDNSOption(PCI_EDNS_OPTION_CODE, struct.pack(PCI_EDNS_OPTION_DATA_FMT, PCI))]
            auth_request = DNSRecord.question(request.q.qname, qtype=QTYPE[request.q.qtype])
            auth_request.add_ar(EDNS0(udp_len=self.udplen, opts=edns_options))
            auth_reply = self.query_authoritative_nameserver(auth_request, ns_ip)
            # reply.add_answer(*cname_rrs, *auth_reply.rr)
            reply.add_answer(*auth_reply.rr)
            if auth_reply.auth:
                reply.add_auth(*auth_reply.auth)
            # else:
            #    reply.add_auth(soa_rr)
        except Exception as exc:
            print("Failed to resolve:", exc)
            reply.header.rcode = RCODE.NXDOMAIN
            if edns_in_request:
                reply.add_ar(EDNS0(udp_len=self.udplen))
        print(f'Ts: {datetime.now().strftime("%Y/%m/%d-%H:%M:%S")}\nReply: {reply}', flush=True)
        return reply


class DNSHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data, connection = self.request
        try:
            rdata = self.get_reply(data)
            connection.sendto(rdata, self.client_address)
        except DNSError as e:
            print(e)

    def get_reply(self, data):
        request = DNSRecord.parse(data)
        resolver = self.server.resolver
        reply = resolver.resolve(request, self)
        rdata = reply.pack()
        return rdata


class UDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer, object):
    def __init__(self, server_address, handler):
        self.allow_reuse_address = True
        self.daemon_threads = True
        if server_address[0] != '' and ':' in server_address[0]:
            self.address_family = socket.AF_INET6
        super(UDPServer, self).__init__(server_address, handler)


class DNSServer(object):
    def __init__(self, resolver,
                 address="0.0.0.0",
                 port=53,
                 handler=DNSHandler,
                 server=None):
        if not server:
            server = UDPServer
        self.server = server((address, port), handler)
        self.server.resolver = resolver
        self.thread = None

    def start(self):
        self.server.serve_forever()

    def start_thread(self):
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.server.shutdown()

    def is_alive(self):
        return self.thread.is_alive()

    def wait(self):
        return self.thread.join()


def main():
    resolver = BaseResolver()
    server = DNSServer(resolver, port=8053, address="0.0.0.0")
    server.start_thread()
    server.wait()


if __name__ == "__main__":
    main()
