import os
import numpy as np
from scapy.utils import RawPcapReader
from aeacus import RESULTS_PATH
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, TCP, UDP



def main():
    file_name = os.path.join(RESULTS_PATH, "aeacus_dump.csv")
    history = {}
    data = []
    for line in open(file_name).readlines()[1:]:
        line = line.strip()
        _, ts, src, src_port, dst, dst_port= line.split(",")[:6]
        ts = float(ts[1:-1])
        src = src[1:-1]
        dst = dst[1:-1]
        if src == '10.0.10.10':
            if dst == '192.168.57.12':
                if ts - history.get(src_port, 0) > 1:
                    history[src_port] = ts
            elif dst == '192.168.57.14':
                sent_ts = history.pop(src_port, 0)
                if sent_ts > 0:
                    data.append(ts - sent_ts)
    print(np.mean(data), np.std(data))


if __name__ == "__main__":
    main()
