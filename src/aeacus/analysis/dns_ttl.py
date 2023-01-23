import asyncio
import json
import os
import traceback

from aeacus import RESOURCE_PATH, RESULTS_PATH
from aeacus.dns.resolver import resolve_name_iteratively_async, resolve_name_recursively_async


async def resolve(domain, results, resolver='127.0.0.53'):
    try:
        if resolver:
            ans = await resolve_name_iteratively_async(domain, resolver)
        else:
            ans = await resolve_name_recursively_async(domain)
        ans = ans[2]
        results[domain] = ans
    except Exception as e:
        traceback.print_exc()
        results[domain] = ('', '')
        print(f'No result for {domain}: {e}')


async def main():
    path = os.path.join(RESOURCE_PATH, 'alexa_top_500.txt')
    domains = open(path).readlines()
    domains = [d.strip() for d in domains]
    domains = ['douyu.com']
    domains = ['test.test.xuebing.me']
    data = {}
    loop = asyncio.get_event_loop()
    step = 100
    for i in range(0, len(domains), step):
        for d in domains[i: i + step]:
            # loop.create_task(resolve(d, data, resolver="1.1.1.1"))
            loop.create_task(resolve(d, data, resolver=None))
        await asyncio.sleep(1)
    await asyncio.sleep(1)
    print(f'{len(data)} domains have been queried')
    with open(os.path.join(RESULTS_PATH, 'dns_ttl_ns.json'), 'w') as f:
        json.dump(data, f)


def illustrate():
    pass


if __name__ == '__main__':
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    illustrate()
