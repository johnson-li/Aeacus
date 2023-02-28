import os.path
import re

import numpy as np

from aeacus import *
from aeacus.analysis.dns_ttl import draw_cdf

results_path = RESULTS3_PATH


def main():
    dataset = {'cloud': {'dns': {}, 'aeacus': {}}, 'edge': {'dns': {}, 'aeacus': {}}}
    for s in dataset.keys():
        for ss in ['dns', 'aeacus']:
            path = os.path.join(results_path, f'handshake_delay_{s}_{ss}.log')
            data = dataset[s][ss]
            for l in open(path).readlines():
                l = l.strip()
                if 'DNS query sent' in l:
                    ts = re.compile('\\[(\\d+)\\]').match(l)[1]
                    ts = int(ts[1: -1])
                    data[ts] = -1
                elif 'Handshake succeeded' in l:
                    ts = re.compile('\\[(\\d+)\\]').match(l)[1]
                    ts = int(ts[1: -1])
                    delay = re.compile('.*delay: ([-0-9.]*) ms').match(l)[1]
                    delay = float(delay)
                    data[ts] = delay
            success_ratio = len(list(filter(lambda x: x >= 0, data.values()))) / len(data)
            print(f'[{s}, {ss}] Count: {len(data)}, success ratio: {success_ratio * 100:.01f} %')
    for s in dataset.keys():
        values = []
        legend = []
        for ss in ['DNS', 'Aeacus']:
            d = list(filter(lambda x: x > 0, dataset[s][ss.lower()].values()))
            values.append(d)
            legend.append(f'{ss}')
            print(f'[{s}, {ss}] Mean: {np.mean(d)}, min: {np.min(d)}, median: {np.median(d)}, variance: {np.std(d)}')
        dns, aeacus = np.mean(values[0]), np.mean(values[1])
        print(f'[{s}] Aeacus reduction: {dns - aeacus} ms ({(dns - aeacus) / dns * 100}%)')
        draw_cdf(values, 'Handshake delay (ms)', f'handshake_delay_{s}.pdf', legend, limit=150)
    # dns_mean = np.mean(list(dns_data.values()))
    # aeacus_mean = np.mean(list(aeacus_data.values()))
    # print(f'DNS: {dns_mean}, Aeacus: {aeacus_mean}, reduction: {dns_mean - aeacus_mean} ({(dns_mean - aeacus_mean) / dns_mean * 100}%)')


if __name__ == '__main__':
    main()
