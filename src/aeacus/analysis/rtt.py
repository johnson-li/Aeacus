import asyncio
import json
import os
import socket

from aeacus import RESOURCE_PATH
from icmplib import resolve, multiping
from icmplib.models import Host

from aeacus.dns.resolver import resolve_name_iteratively_async


async def resolve_domain_names(domain_names):
    res = {}
    for i, d in enumerate(domain_names):
        try:
            a = await resolve_name_iteratively_async(d, resolver="127.0.0.53")
            res[d] = str(a[1])
            print(f'[{i}] {d}: {a[1]}')
        except Exception as e:
            print(e)
    json.dump(res, open(os.path.join(RESOURCE_PATH, 'alexa_top_500_ip.json'), 'w+'))
    return res


def dump_resolved_ip():
    domains = open(os.path.join(RESOURCE_PATH, 'alexa_top_500.txt')).readlines()
    domains = [d.strip() for d in domains]
    asyncio.run(resolve_domain_names(domains))


def measure_rtt_to_server():
    data = json.load(open(os.path.join(RESOURCE_PATH, 'alexa_top_500_ip.json')))
    domains = list(data.keys())
    ips = [data[d] for d in domains]
    res = multiping(ips, count=10, interval=0.1)
    data = {}
    for i, r in enumerate(res):
        r: Host = r
        assert ips[i] == r.address
        if r.min_rtt > 0:
            data[domains[i]] = r.min_rtt
    json.dump(data, open(os.path.join(RESOURCE_PATH, 'alexa_top_500_rtt.json'), 'w+'))


def measure_rtt_to_ns():
    pass


def draw_diagram():
    rtt_data = json.load(open(os.path.join(RESOURCE_PATH, 'alexa_top_500_rtt.json')))
    print(len(rtt_data))


def main():
    # dump_resolved_ip()
    # measure_rtt_to_server()
    draw_diagram()


if __name__ == '__main__':
    main()
