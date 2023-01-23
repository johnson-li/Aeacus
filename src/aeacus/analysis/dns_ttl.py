import asyncio
import json
import os
import traceback

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from aeacus import RESOURCE_PATH, RESULTS_PATH, DIAGRAM_PATH
from aeacus.dns.resolver import resolve_name_iteratively_async, resolve_name_recursively_async, CACHE
from scipy.interpolate import make_interp_spline, BSpline

test_cases = [(None, 'ns'), ('1.1.1.1', 'public_dns'), ('127.0.0.53', 'ldns')]


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


async def main():
    for i in range(10):
        for tc in test_cases[1:]:
            await collect_ttl_data(*tc)


def draw_cdf(values, x_label, name, legend):
    font_size = 16
    fig, ax = plt.subplots(figsize=(4, 2.5))
    for value in values:
        value = np.array(value)
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
    plt.legend(legend)
    matplotlib.rcParams.update({'font.size': font_size})
    ax.tick_params(axis='both', which='major', labelsize=font_size)
    ax.tick_params(axis='both', which='minor', labelsize=font_size)
    plt.xlabel(x_label, size=font_size)
    plt.xlim([0, 10 * 60])
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
        dataset.append(data)
    draw_cdf(dataset, 'DNS TTL (s)', f"dns_ttl.pdf", [t[1] for t in test_cases])


if __name__ == '__main__':
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # asyncio.run(main())
    illustrate()
