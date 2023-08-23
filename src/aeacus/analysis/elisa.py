import json
import os
import re
import numpy as np
import matplotlib.pyplot as plt

from aeacus import RESOURCE_PATH, RESULTS_PATH


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

    reduction_list = []
    error_list = [[], []]
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
        if np.any(improve > 100):
            print('asdf', improve)
        value = np.percentile(improve, 50)
        print(f"{domain}: Aeacus reduces delay by {value:.2f}%, data set size: {len(ts_list)}")
        # if value < 0:
        #     print(delay_dns, delay_aeacus)
        reduction_list.append(value)
        error_list[0].append(value - np.percentile(improve, 20))
        error_list[1].append(np.percentile(improve, 80) - value)
    print(reduction_list, error_list)
    plt.bar(np.arange(len(reduction_list)), reduction_list, yerr=np.vstack(error_list))
    plt.xlabel('Domain')
    plt.ylabel('Reduction in connection setup delay (%)')
    plt.savefig(os.path.join(RESULTS_PATH, "eval_elisa_delay_reduction.pdf"))


    ns_delay_data = json.load(open(os.path.join(RESULTS_PATH, 'dns_ns_delay.json')))
    srv_rtt_data = json.load(open(os.path.join(RESOURCE_PATH, 'alexa_top_500_rtt.json')))

    ns_delay = []
    srv_rtt = []
    for domain in data:
        if domain in ns_delay_data and domain in srv_rtt_data:
            ns_delay.append(ns_delay_data[domain]['delay'] * 1000)
            srv_rtt.append(srv_rtt_data[domain])
    print(len(ns_delay))
    for p in [10, 20, 50, 80, 90, 100]:
        print(p, np.percentile(ns_delay, p), np.percentile(srv_rtt, p))
    print(np.sort(ns_delay))


if __name__ == '__main__':
    main()
