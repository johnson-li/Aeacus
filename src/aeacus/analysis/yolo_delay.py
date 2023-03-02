import os.path
import re

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from aeacus import RESULTS_PATH


def main():
    data = {}
    path = os.path.join(RESULTS_PATH, "yolo_delay.log")
    for l in open(path).readlines():
        l = l.strip()
        if l:
            m = re.compile('\\[(\\d+)\\] Delay: ([0-9.]+)').match(l)
            if m:
                n = int(m[1])
                delay = float(m[2])
                data.setdefault(n, []).append(delay)
    keys = list(sorted(data.keys()))
    data = [np.median(data[k]) for k in keys]
    fig, ax = plt.subplots(figsize=(3.5, 2))
    font_size = 16
    plt.plot(keys, data, linewidth=3)
    matplotlib.rcParams.update({'font.size': font_size})
    ax.tick_params(axis='both', which='major', labelsize=font_size)
    ax.tick_params(axis='both', which='minor', labelsize=font_size)
    plt.xlabel('Concurrent tasks', size=font_size)
    plt.ylabel('Delay (s)', size=font_size)
    fig.tight_layout(pad=.7)
    plt.savefig(os.path.join(RESULTS_PATH, "yolo_delay.pdf"))
    plt.close()


if __name__ == '__main__':
    main()
