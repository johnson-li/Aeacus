import os
import re
import numpy as np
from matplotlib import pyplot as plt

from aeacus import RESULTS_PATH, DIAGRAM_PATH


def load_result(path):
    data = []
    with open(path) as f:
        for line in f.readlines():
            line = line.strip()
            m = re.search('handshake completed in ([0-9.]+)ms', line)
            if m:
                data.append(float(m.group(1)))
    return data


def main():
    direct = load_result(os.path.join(RESULTS_PATH, "upf_benchmark_direct.log"))
    aeacus = load_result(os.path.join(RESULTS_PATH, "upf_benchmark_aeacus.log"))
    p = 50
    print(np.percentile(direct, p), np.percentile(aeacus, p))
    plt.boxplot([direct, aeacus])
    plt.savefig(os.path.join(DIAGRAM_PATH, f'benchmark.pdf'))
    plt.close()

    x = [10, 20, 50, 80, 100, 200, 300, 500]
    y1 = [[], []]
    y2 = [[], []]
    for i in x:
        direct = load_result(os.path.join(RESULTS_PATH, f"upf_benchmark_parallel_{i}_direct.log"))
        aeacus = load_result(os.path.join(RESULTS_PATH, f"upf_benchmark_parallel_{i}_aeacus.log"))
        y1[0].append(np.mean(direct))
        y1[1].append(np.var(direct))
        y2[0].append(np.mean(aeacus))
        y2[1].append(np.var(aeacus))
    print(y1)
    print(y2)
    plt.plot(x, y1[0])
    plt.plot(x, y2[0])
    plt.legend(['Direct connection', 'Aeacus'])
    plt.xlabel('Number of concurrent connections')
    plt.ylabel('Handshake Delay (ms)')
    plt.savefig(os.path.join(DIAGRAM_PATH, f'benchmark_parallel.pdf'))


if __name__ == '__main__':
    main()
