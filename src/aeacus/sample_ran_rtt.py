import os
import random
import re

from aeacus import RESULTS1_PATH


def load_rtt_data(server):
    path = os.path.join(RESULTS1_PATH, f'rtt_{server}.log')
    data = {}
    for l in open(path).readlines():
        l = l.strip()
        if l:
            ts = int(re.compile('\\[(\\d+)\\]').match(l)[1])
            data[ts] = -1
            if 'Send RTT query' in l:
                data[ts] = -1
            elif 'Receive RTT response' in l:
                delay = re.compile('.*delay: ([-0-9.]*) ms').match(l)[1]
                delay = float(delay)
                data[ts] = delay
    return data


def main():
    rtt_data = load_rtt_data('edge')
    rtt_data = list(rtt_data.values())
    print(int(random.choice(rtt_data)))


if __name__ == '__main__':
    main()
