import os
import re
import numpy as np

from aeacus import RESULTS_PATH


def main():
    folder = os.path.join(RESULTS_PATH, "eval_elisa")
    data = {}
    for filename in os.listdir(folder):
        if not filename.endswith(".txt"):
            continue
        ts, domain, sys = filename[:-4].split("_")
        path = os.path.join(folder, filename)
        with open(path) as f:
            log = f.read()
            s = re.search(r"handshake completed in (\d+.?\d+)ms", log)
            delay = -1
            if s:
                delay = float(s.group(1))
            s = re.search(r'It takes (\d+.?\d+)ms to resolve', log)
            dns_delay = -1
            if s:
                dns_delay = float(s.group(1))
            data.setdefault(domain, {})
            data[domain].setdefault(ts, {})
            data[domain][ts][sys] = delay
            if dns_delay > 0:
                data[domain][ts]["dns_query"] = dns_delay
            else:
                data[domain][ts].setdefault("dns_query", -1)
    for domain in data:
        ts_list = sorted(data[domain].keys())
        ts_list = [ts for ts in ts_list if data[domain][ts]["dns_query"] > 0]
        if not ts_list:
            continue
        delay_aeacus = np.array([data[domain][ts]["aeacus"] for ts in ts_list])
        delay_dns = np.array([data[domain][ts]["dns"] for ts in ts_list])
        print('Successful connection, ', np.sum(delay_aeacus > 0), np.sum(delay_dns > 0))
        indexes = np.logical_and(delay_aeacus > 0, delay_dns > 0)
        delay_aeacus = delay_aeacus[indexes]
        delay_dns = delay_dns[indexes]
        improve = (delay_dns - delay_aeacus) / delay_dns * 100
        value = np.percentile(improve, 10)
        print(f"{domain}: Aeacus reduces delay by {value:.2f}%, data set size: {len(ts_list)}")




if __name__ == '__main__':
    main()
