import os
import re

import numpy as np

from aeacus import RESULTS_PATH


def main():
    path = os.path.join(RESULTS_PATH, "eval_0-rtt")
    data = {}
    for f in os.listdir(path):
        domain = f.split('_')[1]
        zero_rtt = '0-rtt' in f
        early_data = False
        hs_delay = 0
        query_delay = 0
        f = os.path.join(path, f)
        for l in open(f).readlines():
            if len(l) > 200:
                continue
            if 'Early data: true' in l:
                early_data = True
            m = re.search(r'.*\[(.*)ms\] got response headers.*', l)
            if m:
                query_delay = float(m.group(1))
                break
        if query_delay > 0:
            data.setdefault(domain, {'0-rtt': [], '1-rtt': []})
            t = '0-rtt' if early_data else '1-rtt'
            data[domain][t].append(query_delay)
    total = 108
    print(len(data))
    sites = [k for k, v in data.items() if len(v['0-rtt']) > 0 and len(v['1-rtt']) > 0]
    print(len(sites) / total, len(sites))
    smaller = [np.median(v['0-rtt']) <= np.median(v['1-rtt']) for k, v in data.items() if len(v['0-rtt']) > 0 and len(v['1-rtt']) > 0]
    print(np.count_nonzero(smaller) / len(smaller), np.count_nonzero(smaller))


if __name__ == '__main__':
    main()
