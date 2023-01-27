import asyncio
import json
import os.path

from dnslib import DNSLabel, RR, QTYPE, SOA

from aeacus.dns_legacy_aio import UdpServerProtocol

DATA_PATH = '/tmp/dns_aeacus.json'


class BaseResolver(object):
    def load_data(self):
        if os.path.exists(DATA_PATH):
            data = json.load(open(DATA_PATH))
            data = {DNSLabel(k): v for k, v in data.items()}
        else:
            data = {}
        return data

    async def resolve(self, request):
        domain_name = request.q.qname
        reply = request.reply()
        reply.add_auth(RR("aeacus.xuebing.me", QTYPE.SOA, ttl=60,
                          rdata=SOA("mobix.xuebing.me", "admin.xuebing.me", (20140101, 3600, 3600, 3600, 3600))))
        if request.q.qtype == QTYPE.A:
            data = self.load_data()
            ip = data.get(domain_name, None)
            if ip:
                reply.add_answer(*RR.fromZone(f'{domain_name} 60 IN A {ip}'))
        return reply


async def main():
    loop = asyncio.get_running_loop()
    resolver = BaseResolver()
    await loop.create_datagram_endpoint(
        lambda: UdpServerProtocol(resolver),
        local_addr=('195.148.127.230', 53))
    await asyncio.sleep(10000)


if __name__ == "__main__":
    asyncio.run(main())
