import socket

from dnslib import DNSRecord, DNSError
from dnslib.dns import QTYPE


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
