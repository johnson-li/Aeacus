import os
import re

import numpy as np

from aeacus import RESULTS_PATH


def main():
    file = os.path.join(RESULTS_PATH, "quic-resolver.log")
    data = []
    for line in open(file).readlines():
        line = line.strip()    
        s = re.search(r"(\d+.\d+)µs", line)
        if s:
            data.append(float(s.group(1)) / 1000)
        s = re.search(r"(\d+.\d+)ms", line)
        if s:
            data.append(float(s.group(1)))
    print(np.mean(data))


if __name__ == "__main__":
    main()
