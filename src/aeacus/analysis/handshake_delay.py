import os.path
import re

from aeacus import RESULTS_PATH
from aeacus.analysis.dns_ttl import draw_cdf


def main():
    aeacus_data = {}
    dns_data = {}
    for system, data in [('dns', dns_data), ('aeacus', aeacus_data)]:
        path = os.path.join(RESULTS_PATH, f'handshake_delay_{system}.log')
        for l in open(path).readlines():
            l = l.strip()
            if 'DNS query sent' in l:
                ts = re.compile('\\[(\\d+)\\]').match(l)[1]
                ts = int(ts[1: -1])
                data[ts] = -1
            elif 'Handshake succeeded' in l:
                ts = re.compile('\\[(\\d+)\\]').match(l)[1]
                ts = int(ts[1: -1])
                delay = re.compile('.*delay: ([0-9.]*) ms').match(l)[1]
                delay = float(delay)
                data[ts] = delay
        success_ratio = len(list(filter(lambda x: x >= 0, data.values()))) / len(data)
        print(f'[{system}] Count: {len(data)}, success ratio: {success_ratio * 100:.01f} %')
    draw_cdf([dns_data.values(), aeacus_data.values()], 'Handshake delay (ms)', 'handshake_delay.pdf', ['DNS', 'Aeacus'])


if __name__ == '__main__':
    main()
