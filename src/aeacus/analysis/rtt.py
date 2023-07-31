import asyncio
import json
import os
import socket

import numpy as np

from aeacus import RESOURCE_PATH
from icmplib import resolve, multiping
from icmplib.models import Host
from dnslib import DNSRecord, EDNS0, DNSLabel
from aeacus.analysis.dns_ttl import draw_cdf

from aeacus.dns.resolver import resolve_name_iteratively_async, resolve_ns_async


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


async def resolve_domain_names_ns(domain_names):
    res = {}
    for i, d in enumerate(domain_names):
        try:
            _, ns_name, _ = await resolve_ns_async(DNSLabel(d))
            _, ns_ip, _ = await resolve_name_iteratively_async(DNSLabel(ns_name), resolver="127.0.0.53")
            res[d] = {'name': str(ns_name), 'ip': str(ns_ip)}
            print(f'[{i}] {d}: {res[d]}')
        except Exception as e:
            print(e)
    json.dump(res, open(os.path.join(RESOURCE_PATH, 'alexa_top_500_ns_ip.json'), 'w+'))
    return res


def dump_resolved_ip():
    domains = open(os.path.join(RESOURCE_PATH, 'alexa_top_500.txt')).readlines()
    domains = [d.strip() for d in domains]
    # asyncio.run(resolve_domain_names(domains))
    asyncio.run(resolve_domain_names_ns(domains))


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
    data = json.load(open(os.path.join(RESOURCE_PATH, 'alexa_top_500_ns_ip.json')))
    domains = list(data.keys())
    ips = [data[d]['ip'] for d in domains]
    res = multiping(ips, count=10, interval=0.1)
    data = {}
    for i, r in enumerate(res):
        r: Host = r
        assert ips[i] == r.address
        if r.min_rtt > 0:
            data[domains[i]] = r.min_rtt
    json.dump(data, open(os.path.join(RESOURCE_PATH, 'alexa_top_500_ns_rtt.json'), 'w+'))


def draw_diagram():
    rtt_data = json.load(open(os.path.join(RESOURCE_PATH, 'alexa_top_500_rtt.json')))
    ns_rtt_data = json.load(open(os.path.join(RESOURCE_PATH, 'alexa_top_500_ns_rtt.json')))
    for rtt_ran in [10, 100]:
        hit_list = []
        ue_miss_list = []
        ldns_miss_list = []
        for d in rtt_data.keys():
            if d in ns_rtt_data:
                hit_list.append(rtt_data[d] + rtt_ran)
                ue_miss_list.append(rtt_data[d] + rtt_ran * 2)
                ldns_miss_list.append(ns_rtt_data[d] + rtt_data[d] + rtt_ran * 2)
        draw_cdf([hit_list, ue_miss_list, ldns_miss_list], 'Connection Setup Delay (ms)', 
                f'alexa_top_500_rtt_ran_{rtt_ran}.pdf', 
                ['Cache hit', 'Cache miss (UE)', 'Cache miss (LDNS)'] if rtt_ran == 10 else None, 
                limit=700, figsize=(4, 3))
        hit_list = np.array(hit_list)
        ue_miss_list = np.array(ue_miss_list)
        ldns_miss_list = np.array(ldns_miss_list)
        ldns_hit = (ue_miss_list - hit_list) / hit_list * 100
        ldns_miss = (ldns_miss_list - hit_list) / hit_list * 100
        print(f'[{rtt_ran}] LDNS hit: {np.mean(ldns_hit), np.max(ldns_hit)}'
              f', miss: {np.median(ldns_miss), np.max(ldns_miss)}')


def main():
    # dump_resolved_ip()
    # measure_rtt_to_server()
    # measure_rtt_to_ns()
    draw_diagram()


if __name__ == '__main__':
    main()
