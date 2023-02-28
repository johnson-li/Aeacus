import os.path
import re

import numpy as np

from aeacus import RESULTS_PATH

CLOUD_IP = "34.118.22.129"
EDGE_IP = "195.148.127.230"


def load_upf_eval_data():
    path = os.path.join(RESULTS_PATH, "upf_eval.log")
    rounds = []
    eval_round = {}
    platform = 'cloud'
    domain_index = 0
    for l in open(path).readlines():
        l = l.strip()
        if l:
            match = re.compile("Sample RTT: (\\d+)").match(l)
            if match:
                if eval_round:
                    rounds.append(eval_round)
                eval_round = {'RAN RTT': int(match[1]), 'Dig': {}, 'cloud': {'Aeacus': {}, 'DNS': {}},
                              'edge': {'Aeacus': {}, 'DNS': {}}}
                continue
            match = re.compile("Sample domain name: (\\d+).*").match(l)
            if match:
                domain_index = int(match[1])
                continue
            match = re.compile(".*\\[https://([0-9.]+):4433/\\] handshake completed in ([.0-9]+)ms").match(l)
            if match:
                ip = match[1]
                delay = float(match[2])
                server = 'edge' if ip == EDGE_IP else 'cloud'
                eval_round[server][platform].setdefault(domain_index, []).append(delay)
                continue
            match = re.compile(";; Query time: ([0-9]+) msec").match(l)
            if match:
                eval_round['Dig'].setdefault(domain_index, []).append(int(match[1]))
                continue
            if l == 'Evaluate DNS':
                platform = 'DNS'
                continue
            if l == 'Evaluate Aeacus':
                platform = 'Aeacus'
                continue
    if eval_round:
        rounds.append(eval_round)
    return rounds


def analyse(server):
    rounds = load_upf_eval_data()
    print(f'Rounds: {len(rounds)}')
    data = {'Aeacus': [], 'DNS': []}
    data = {'edge': data.copy(), 'cloud': data.copy()}
    data = {'h': data.copy(), 'mh': data.copy(), 'mm1': data.copy(), 'mm2': data.copy()}
    for r in rounds:
        dns_delay = r['Dig']
        ran_delay = r['RAN RTT']
        handshake_delay = r[server]
        print(dns_delay)
        print(handshake_delay)
        keys = list(dns_delay.keys())

        for k in keys:
            # if k not in handshake_delay['DNS']:
            #     continue
            data['h'][server]['DNS'].append(handshake_delay['DNS'][k])
            data['mh'][server]['DNS'].append([d + ran_delay for d in handshake_delay['DNS'][k]])
            data['mm1'][server]['DNS'].append([sum(x) for x in zip(dns_delay[k], handshake_delay['DNS'][k])])
            data['mm2'][server]['DNS'].append([sum(x) for x in zip(dns_delay[k], handshake_delay['DNS'][k])])
            aeacus_h = handshake_delay['Aeacus'][k]
            aeacus_mh = handshake_delay['Aeacus'][k]
            aeacus_mm1 = handshake_delay['Aeacus'][k]
            data['mm2'][server]['Aeacus'].append(handshake_delay['Aeacus'][k])

        # dns_st = [(np.median(dns_delay[k]), np.std(dns_delay[k])) for k in keys]
        # hs_aeacus_st = [(np.median(handshake_delay['Aeacus'][k]), np.std(handshake_delay['Aeacus'][k])) for k in keys]
        # hs_dns_st = [(np.median(handshake_delay['DNS'][k]), np.std(handshake_delay['DNS'][k])) for k in keys]
        # setup_data = [(sum(x) for x in zip(dns_delay[k], handshake_delay[k])) for k in keys]
        # setup_dns_st = [(np.median(d), np.std(d)) for d in setup_data]
        #
        # data['h'][server]['Aeacus'] += hs_aeacus_st
        # data['h'][server]['DNS'] += hs_dns_st
        # data['mh'][server]['Aeacus'] = 0
        # data['mh'][server]['DNS'] = 0
        # data['mm1'][server]['Aeacus'] = 0
        # data['mm1'][server]['DNS'] = 0
        # data['mm2'][server]['Aeacus'] = 0
        # data['mm2'][server]['DNS'] = 0


def main():
    analyse('edge')
    # analyse('cloud')


if __name__ == '__main__':
    main()
