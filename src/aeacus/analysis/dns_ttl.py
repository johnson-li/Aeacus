import asyncio
import json
import os
import time
import traceback

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from dnslib import DNSRecord, EDNS0, DNSLabel

from aeacus import RESOURCE_PATH, RESULTS_PATH, DIAGRAM_PATH
from aeacus.dns.resolver import resolve_name_iteratively_async, resolve_name_recursively_async, CACHE, resolve_ns_async, \
    send_with_retry_async

# test_cases = [(None, 'ns'), ('1.1.1.1', 'public_dns'), ('127.0.0.53', 'ldns')]
# test_cases = [(None, 'ns'), ('127.0.0.53', 'ldns')]
test_cases = [(None, 'ns'), ]


async def resolve(domain, results, resolver='127.0.0.53'):
    results.setdefault(domain, -1)
    try:
        if resolver:
            ans = await resolve_name_iteratively_async(domain, resolver)
            if ans[2] > results[domain]:
                ans = ans[2]
                results[domain] = ans
        else:
            ans = await resolve_name_recursively_async(domain)
            ans = ans[2]
            results[domain] = ans
    except Exception as e:
        traceback.print_exc()
        print(f'No result for {domain}: {e}')


async def collect_ttl_data(resolver, title):
    CACHE.clear()
    domains = open(os.path.join(RESOURCE_PATH, 'alexa_top_500.txt')).readlines()
    domains = [d.strip() for d in domains]
    path = os.path.join(RESULTS_PATH, f'dns_ttl_{title}.json')
    if os.path.exists(path):
        data = json.load(open(path))
    else:
        data = {}
    loop = asyncio.get_event_loop()
    step = 10
    for i in range(0, len(domains), step):
        for d in domains[i: i + step]:
            loop.create_task(resolve(d, data, resolver=resolver))
        await asyncio.sleep(1)
    await asyncio.sleep(1)
    print(f'{len(data)} domains have been queried')
    with open(path, 'w') as f:
        json.dump(data, f)


async def measure_delay(data):
    ns = data['ns']
    ns_ip = await resolve_name_iteratively_async(ns, resolver="127.0.0.53")
    a_request = DNSRecord.question("example.org", "A")
    a_request.add_ar(EDNS0(udp_len=1024))
    ts = time.time()
    await send_with_retry_async(a_request, (ns_ip[1], 53))
    data['delay'] = time.time() - ts


async def collect_ns_delay():
    domains = open(os.path.join(RESOURCE_PATH, 'alexa_top_500.txt')).readlines()
    domains = [d.strip() for d in domains]
    data = {}
    ns_list = list(filter(lambda x: x, [CACHE.get((DNSLabel(d), 'NS', 'IN'), None) for d in domains]))
    ns_list = [ns[1] for ns in ns_list]
    loop = asyncio.get_event_loop()
    step = 10
    for i in range(0, len(ns_list), step):
        for domain, ns in zip(domains[i: i + step], ns_list[i: i + step]):
            data[domain] = {'ns': str(ns), 'delay': -1}
            loop.create_task(measure_delay(data[domain]))
        await asyncio.sleep(1)
    json.dump({str(k): v for k, v in data.items()}, open(os.path.join(RESULTS_PATH, 'dns_ns_delay.json'), 'w+'))


def draw_cdf(values, x_label, name, legend, limit=-1, figsize=(4, 2.3)):
    font_size = 16
    fig, ax = plt.subplots(figsize=figsize)
    for k, value in enumerate(values):
        value = np.array(list(value))
        value.sort()
        y = np.arange(0, 1, 1 / value.shape[0])
        y_new = []
        x_new = []
        for i in range(value.shape[0]):
            v = value[i]
            if not x_new or v != x_new[-1]:
                x_new.append(v)
                y_new.append(y[i])
            elif v == x_new[-1] and y[i] > y_new[-1]:
                y_new[-1] = y[i]
        line='-'
        if k == 1:
            line = '--'
        elif k == 2:
            line = ':'
        plt.plot(x_new, y_new, line, linewidth=3)
    if legend:
        plt.legend(legend, loc='lower right')
    matplotlib.rcParams.update({'font.size': font_size})
    ax.tick_params(axis='both', which='major', labelsize=font_size)
    ax.tick_params(axis='both', which='minor', labelsize=font_size)
    plt.xlabel(x_label, size=font_size)
    if limit > 0:
        plt.xlim([0, limit])
    plt.ylabel('CDF', size=font_size)
    plt.ylim([0, 1])
    fig.tight_layout()
    # if avg:
    #     plt.plot(np.mean(values).repeat(values.shape[0]), np.arange(0, 1, 1 / values.shape[0]), 'g--', linewidth=2)
    plt.savefig(os.path.join(DIAGRAM_PATH, f'{name}'), dpi=600)
    plt.close(fig)


def illustrate():
    dataset = []
    for _, title in test_cases:
        path = os.path.join(RESULTS_PATH, f'dns_ttl_{title}.json')
        data = json.load(open(path))
        data = list(filter(lambda x: x > 0, data.values()))
        print(f'[{title}] Data size: {len(data)}')
        print(np.percentile(data, 80))
        dataset.append(data)
    draw_cdf(dataset, 'DNS TTL (s)', f"dns_ttl.pdf", ['Name Server', 'Resolver'], limit=1000, figsize=(4, 3))

    path = os.path.join(RESULTS_PATH, f'dns_ns_delay.json')
    data = json.load(open(path))
    data = [d * 1000 for d in data.values() if d > 0]
    print(f'Data size: {len(data)}, median: {np.median(data)}')
    print(np.percentile(data, 34))
    dataset = [data]
    draw_cdf(dataset, 'RTT (ms)', f"dns_ns_delay.pdf", [])

    ns_ttl_data = json.load(open(os.path.join(RESULTS_PATH, 'ns_ttl.json')))
    ns_ttl = [d['NS TTL'] / 3600 for d in ns_ttl_data.values() if d['NS TTL'] > 0]
    ns_a_ttl = [d['NS_A TTL'] / 3600 for d in ns_ttl_data.values() if d['NS_A TTL'] > 0]
    print(f'==== NS TTL ====')
    print(np.percentile(ns_ttl, 10), np.percentile(ns_a_ttl, 10))
    draw_cdf([ns_ttl, ns_a_ttl], 'DNS Cache TTL (hours)', f"ns_ttl.pdf", ['NS Record', 'A Record'], figsize=(4, 3))


async def main():
    for i in range(1):
        for tc in test_cases:
            await collect_ttl_data(*tc)
    await collect_ns_delay()
    

async def collect_ns_ttl():
    CACHE.clear()
    domains = open(os.path.join(RESOURCE_PATH, 'alexa_top_500.txt')).readlines()
    domains = [d.strip() for d in domains]
    data = {}
    for d in domains:
        try:
            domain = DNSLabel(d)
            ns = await resolve_ns_async(domain)
            _, ns_ip, ns_ttl = ns
            ns_ip = str(ns_ip)
            a = await resolve_name_recursively_async(ns_ip)
            _, _, a_ttl = a
            data[d] = {'NS IP': ns_ip, 'NS TTL': ns_ttl, 
                       'NS_A TTL': a_ttl}
            print(f'{domain}: {data[d]}')
        except Exception as e:
            print(e)
    json.dump(data, open(os.path.join(RESULTS_PATH, 'ns_ttl.json'), 'w+'))
    


if __name__ == '__main__':
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    # asyncio.run(collect_ns_ttl())
    # illustrate()
