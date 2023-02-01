import asyncio
import json
import os.path

from dnslib import DNSLabel, RR, QTYPE, SOA

from aeacus.dns_legacy_aio import UdpServerProtocol


class BaseResolver(object):
    def load_data(self, path):
        if os.path.exists(path):
            data = json.load(open(path))
            data = {DNSLabel(k): v for k, v in data.items()}
        else:
            data = {}
        return data

    def load_a_data(self):
        return self.load_data('/tmp/dns_aeacus.json')

    def load_txt_data(self):
        return self.load_data('/tmp/dns_aeacus_txt.json')

    async def resolve(self, request):
        domain_name = request.q.qname
        reply = request.reply()
        reply.add_auth(RR("aeacus.xuebing.me", QTYPE.SOA, ttl=60,
                          rdata=SOA("mobix.xuebing.me", "admin.xuebing.me", (20140101, 3600, 3600, 3600, 3600))))
        if request.q.qtype == QTYPE.A:
            data = self.load_a_data()
            ip = data.get(domain_name, None)
            if ip:
                reply.add_answer(*RR.fromZone(f'{domain_name} 60 IN A {ip}'))
        elif request.q.qtype == QTYPE.TXT:
            data = self.load_txt_data()
            txt = data.get(domain_name, None)
            if txt:
                reply.add_answer(*RR.fromZone(f'{domain_name} 60 IN TXT "{txt}"'))
        return reply


async def main():
    loop = asyncio.get_running_loop()
    resolver = BaseResolver()
    await loop.create_datagram_endpoint(
        lambda: UdpServerProtocol(resolver),
        local_addr=('195.148.127.230', 53))
    await asyncio.sleep(100000000)


if __name__ == "__main__":
    asyncio.run(main())
