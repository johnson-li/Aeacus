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
from aeacus.dns.resolver import resolve_name_iteratively_async, resolve_name_recursively_async, CACHE, \
    send_with_retry_async
from scipy.interpolate import make_interp_spline, BSpline

# test_cases = [(None, 'ns'), ('1.1.1.1', 'public_dns'), ('127.0.0.53', 'ldns')]
test_cases = [(None, 'ns')]


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


async def measure_delay(data, ns):
    data.setdefault(ns, -1)
    ns_ip = await resolve_name_iteratively_async(ns, resolver="127.0.0.53")
    a_request = DNSRecord.question("example.org", "A")
    a_request.add_ar(EDNS0(udp_len=1024))
    ts = time.time()
    await send_with_retry_async(a_request, (ns_ip[1], 53))
    data[ns] = time.time() - ts


async def collect_ns_delay():
    domains = open(os.path.join(RESOURCE_PATH, 'alexa_top_500.txt')).readlines()
    domains = [d.strip() for d in domains]
    data = {}
    ns_list = list(filter(lambda x: x, [CACHE.get((DNSLabel(d), 'NS', 'IN'), None) for d in domains]))
    ns_list = [ns[1] for ns in ns_list]
    loop = asyncio.get_event_loop()
    step = 10
    for i in range(0, len(ns_list), step):
        for d in ns_list[i: i + step]:
            loop.create_task(measure_delay(data, ns=d))
        await asyncio.sleep(1)
    json.dump({str(k): v for k, v in data.items()}, open(os.path.join(RESULTS_PATH, 'dns_ns_delay.json'), 'w+'))


def draw_cdf(values, x_label, name, legend, limit=-1):
    font_size = 16
    fig, ax = plt.subplots(figsize=(4, 2))
    for value in values:
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
        x = np.linspace(np.min(x_new), np.max(x_new), 300)
        spl = make_interp_spline(x_new, y_new, 3)
        y = spl(x)
        plt.plot(x_new, y_new, linewidth=2)
    plt.legend(legend, framealpha=.0)
    matplotlib.rcParams.update({'font.size': font_size})
    ax.tick_params(axis='both', which='major', labelsize=font_size)
    ax.tick_params(axis='both', which='minor', labelsize=font_size)
    plt.xlabel(x_label, size=font_size)
    # plt.xlim([0, 10 * 60])
    if limit > 0:
        plt.xlim([0, limit])
    plt.ylabel('CDF', size=font_size)
    plt.ylim([0, 1])
    fig.tight_layout(pad=.3)
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
        print(f'Data size: {len(data)}')
        dataset.append(data)
    draw_cdf(dataset, 'DNS TTL (s)', f"dns_ttl.pdf", ['Authoritative Name Server', 'Public DNS', 'LDNS'])

    path = os.path.join(RESULTS_PATH, f'dns_ns_delay.json')
    data = json.load(open(path))
    data = [d * 1000 for d in data.values() if d > 0]
    print(f'Data size: {len(data)}, median: {np.median(data)}')
    dataset = [data]
    draw_cdf(dataset, 'RTT (ms)', f"dns_ns_delay.pdf", [])


async def main():
    for i in range(1):
        for tc in test_cases:
            await collect_ttl_data(*tc)
    await collect_ns_delay()


if __name__ == '__main__':
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # asyncio.run(main())
    illustrate()
