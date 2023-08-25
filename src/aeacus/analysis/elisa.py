import json
import os
import re
import numpy as np
import matplotlib.pyplot as plt

from aeacus import RESOURCE_PATH, RESULTS_PATH
from aeacus.analysis.dns_ttl import draw_cdf


def main():
    folder = os.path.join(RESULTS_PATH, "eval_elisa")
    rtt_data = json.load(open(os.path.join(RESOURCE_PATH, 'alexa_top_500_rtt.json')))
    ns_rtt_data = json.load(open(os.path.join(RESOURCE_PATH, 'alexa_top_500_ns_rtt.json')))
    data = {}
    rtt_data0 = {}
    pkt_num_count = []
    pkt_round_count = []
    for filename in os.listdir(folder):
        if not filename.endswith(".txt"):
            continue
        ts, domain, sys = filename[:-4].split("_")
        if domain in rtt_data and domain in ns_rtt_data:
            rtt_data0[domain] = rtt_data[domain], ns_rtt_data[domain]
        path = os.path.join(folder, filename)
        pkt_num = 0
        pkt_round = 0
        with open(path) as f:
            log = f.read()
            continual_send = False
            for l in log.split("\n"):
                g = re.search(r"Send \d+ bytes to", l)
                if g:
                    pkt_num += 1
                    if not continual_send:
                        pkt_round += 1
                        continual_send = True
                g = re.search(r"Recv \d+ bytes from", l)
                if g:
                    continual_send = False
                    pkt_num += 1
            s = re.search(r"handshake completed in (\d+.?\d+)ms", log)
            delay = -1
            if s:
                delay = float(s.group(1))
                pkt_num_count.append(pkt_num)
                pkt_round_count.append(pkt_round)
                # if pkt_round == 1:
                #     print(filename)
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
    pkt_round_count = np.array(pkt_round_count)
    print('1-RTT handshake: ', np.sum(pkt_round_count == 1), len(pkt_round_count))
    print(f'Avg pkt num: {np.mean(pkt_num_count)}, avg pkt round: {np.mean(pkt_round_count)}')
    print(f'Min RTT, src: {np.min([rtt_data0[domain][0] for domain in rtt_data0])}'
          f', ns: {np.min([rtt_data0[domain][1] for domain in rtt_data0])}')
    print(f'Max RTT, src: {np.max([rtt_data0[domain][0] for domain in rtt_data0])}'
          f', ns: {np.max([rtt_data0[domain][1] for domain in rtt_data0])}')

    reduction_list = []
    error_list = [[], []]
    reduction_all = []
    reduction_ratio_all = []
    for domain in data:
        ts_list = sorted(data[domain].keys())
        ts_list = [ts for ts in ts_list if data[domain][ts]["dns_query"] > 0]
        if not ts_list:
            continue
        delay_aeacus = np.array([data[domain][ts]["aeacus"] for ts in ts_list])
        delay_dns = np.array([data[domain][ts]["dns"] for ts in ts_list])
        # print(f'Successful connection, aeacus: {np.sum(delay_aeacus > 0)}, dns: {np.sum(delay_dns > 0)}')
        indexes = np.logical_and(delay_aeacus > 0, delay_dns > 0)
        delay_aeacus = delay_aeacus[indexes]
        delay_dns = delay_dns[indexes]
        improvement = delay_dns - delay_aeacus
        improvement_ratio = (delay_dns - delay_aeacus) / delay_dns * 100
        median = np.percentile(improvement_ratio, 50)
        reduction_all.append(np.median(improvement))
        reduction_ratio_all.append(np.median(improvement_ratio))
        # print(f"{domain}: Aeacus reduces delay by "
        #       f"{np.percentile(improvement, 50)} ms ({median:.2f}%), "
        #       f"data set size: {len(ts_list)}")
        top = np.percentile(improvement_ratio, 80)
        bottom = np.percentile(improvement_ratio, 20)
        reduction_list.append(median)
        error_list[0].append(median - bottom)
        error_list[1].append(top - median)
    print(f'Median reduction: {np.median(reduction_all)} ms ({median}%)')
    plt.bar(np.arange(len(reduction_list)), reduction_list, yerr=np.vstack(error_list))
    plt.xlabel('Domain')
    plt.ylabel('Reduction in connection setup delay (%)')
    plt.savefig(os.path.join(RESULTS_PATH, "eval_elisa_delay_reduction.pdf"))

    a = np.array([rtt_data0[domain][0] for domain in rtt_data0])
    b = np.array([rtt_data0[domain][1] for domain in rtt_data0])
    a.sort()
    b.sort()
    draw_cdf([a, b], 'RTT (ms)', f"quic_rtt_cdf.pdf", ['App. Server', 'NS'], figsize=(4, 3), limit=100)

    fig, ax = plt.subplots(figsize=(4, 3))
    ax2 = ax.twinx()
    reduction_all = sorted(reduction_all)
    reduction_ratio_all = sorted(reduction_ratio_all)
    p1, = ax.plot(np.arange(len(reduction_all)) / len(reduction_all), reduction_all, 'r', label='Delay reduction (ms)')
    p2, = ax2.plot(np.arange(len(reduction_ratio_all)) / len(reduction_ratio_all), reduction_ratio_all, 'b', label='Delay reduction ratio (%)')
    ax.set_ylabel('Delay red. (ms)')
    ax2.set_ylabel('Delay red. ratio (%)')
    ax.yaxis.get_label().set_color(p1.get_color())
    ax2.yaxis.get_label().set_color(p2.get_color())
    plt.xlim([0, 1])
    ax.set_xlabel('CDF')
    plt.tight_layout(pad=.1)
    plt.savefig(os.path.join(RESULTS_PATH, "eval_elisa_delay_reduction_cdf.pdf"))
    plt.close(fig)


    ns_delay_data = json.load(open(os.path.join(RESULTS_PATH, 'dns_ns_delay.json')))
    srv_rtt_data = json.load(open(os.path.join(RESOURCE_PATH, 'alexa_top_500_rtt.json')))

    ns_delay = []
    srv_rtt = []
    for domain in data:
        if domain in ns_delay_data and domain in srv_rtt_data:
            ns_delay.append(ns_delay_data[domain]['delay'] * 1000)
            srv_rtt.append(srv_rtt_data[domain])
    # print(len(ns_delay))
    # for p in [10, 20, 50, 80, 90, 100]:
    #     print(p, np.percentile(ns_delay, p), np.percentile(srv_rtt, p))
    # print(np.sort(ns_delay))


if __name__ == '__main__':
    main()
