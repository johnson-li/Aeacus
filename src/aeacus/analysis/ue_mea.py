import json
import os.path
import re

import matplotlib.pyplot as plt
import numpy as np

from aeacus import RESULTS_PATH, DIAGRAM_PATH, RESULTS1_PATH
from aeacus.analysis.dns_ttl import draw_cdf


def main0():
    path = os.path.join(RESULTS_PATH, 'ue_measurements')
    rtt_data = {}
    for f in os.listdir(path):
        p = os.path.join(path, f)
        with open(p) as ff:
            data = json.load(ff)
            data = data['recordSet']
            data = data['UdpPingMeasurement@213070896']
            records = data['records']
            for r in records:
                send_ts, recv_ts = r['sendTs'], r['recvTs']
                if recv_ts > 0:
                    rtt_data[recv_ts] = recv_ts - send_ts
                else:
                    rtt_data[recv_ts] = -1
    rtt_list = np.array(list(rtt_data.values()))
    rtt_list = rtt_list[rtt_list > 0]
    # print(np.min(rtt_list), np.median(rtt_list))


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


def load_cell_data():
    path = os.path.join(RESULTS1_PATH, f'ue.log')
    cell_data = {}
    for l in open(path).readlines():
        l = l.strip()
        l = json.loads(l)
        ts, data = l['ts'], l['data']
        if type(data) == list:
            for d in data:
                cell_info = d['cellInfo']
                if cell_info['connectionStatus'] == 'CONNECTION_PRIMARY_SERVING':
                    # if cell_info['connectionStatus'] == 'CONNECTION_SECONDARY_SERVING':
                    pci = cell_info['identity']['pci']
                    tac = cell_info['identity']['tac']
                    rsrq = cell_info['signalStrength']['rsrq']
                    cell_data[ts] = (pci, rsrq, tac)
    return cell_data


def main():
    cell_data = load_cell_data()
    rtt_data = load_rtt_data('edge')
    rtt_ts_list = np.array(sorted(rtt_data.keys()))
    rtt_list = np.array([rtt_data[t] for t in rtt_ts_list])
    rtt_ts_list = rtt_ts_list[rtt_list > 0]
    rtt_list = rtt_list[rtt_list > 0]
    print(np.min(rtt_list), np.percentile(rtt_list, 99))
    plt.plot(rtt_ts_list, rtt_list)
    # plt.xlim([rtt_ts_list[3300], rtt_ts_list[3370]])
    ts_list = np.array(sorted(cell_data.keys()))
    pci_list = np.array([cell_data[t][0] for t in ts_list])
    rsrq_list = np.array([cell_data[t][1] for t in ts_list])
    tac_list = np.array([cell_data[t][2] for t in ts_list], dtype=float)
    tac_list = tac_list - np.min(tac_list)
    plt.plot(ts_list, pci_list, '.')
    # plt.plot(ts_list, rsrq_list, '*')
    plt.plot(ts_list, tac_list)
    plt.xlabel('Time (ms)')
    plt.ylabel('RTT (ms)')
    # plt.legend(['RTT', 'PCI', 'RSRQ'])
    plt.savefig(os.path.join(DIAGRAM_PATH, 'rtt_edge.pdf'))
    plt.close()

    pci_pre = -1
    ts_pre = -1
    handover_durations = []
    for ts, pci in zip(ts_list, pci_list):
        if pci_pre > 0 and pci != pci_pre and ts - ts_pre < 300:
            handover_durations.append((ts_pre, ts))
        else:
            pci_pre = pci
            ts_pre = ts
    print(len(handover_durations))
    handover_ts_list = []
    handover_rtt_list = []
    non_handover_ts_list = []
    non_handover_rtt_list = []
    duration = 000
    bias = -200
    for ts, rtt in zip(rtt_ts_list, rtt_list):
        is_handover = False
        if handover_durations and ts > handover_durations[0][1] + duration + bias:
            handover_durations.pop()
        for ha_dur in handover_durations:
            if ha_dur[0] - duration + bias <= ts <= ha_dur[1] + duration + bias:
                handover_ts_list.append(ts)
                handover_rtt_list.append(rtt)
                is_handover = True
                break
        if not is_handover:
            non_handover_ts_list.append(ts)
            non_handover_rtt_list.append(rtt)
    print(np.mean(handover_rtt_list), np.mean(non_handover_rtt_list))
    draw_cdf([handover_rtt_list, non_handover_rtt_list], 'RTT (ms)', f'rtt_handover_vs_non.pdf',
             ['During handover', 'Outside handover'], limit=130)


if __name__ == '__main__':
    # main()
    main()
