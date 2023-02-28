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
    platform = 'DNS'
    domain_index = 0
    for l in open(path).readlines():
        l = l.strip()
        if l:
            if l == 'Evaluate DNS':
                platform = 'DNS'
                continue
            if l.startswith('Evaluate Aeacus'):
                platform = 'Aeacus'
                continue
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
            match = re.compile(".*\\[https://([0-9]+).([a-z]+).aeacus:4433/\\] handshake completed in ([.0-9]+)ms").match(l)
            if match:
                domain_index = int(match[1])
                server = match[2]
                delay = float(match[3])
                eval_round[server][platform].setdefault(domain_index, []).append(delay)
                continue
            match = re.compile(";; Query time: ([0-9]+) msec").match(l)
            if match:
                eval_round['Dig'].setdefault(domain_index, []).append(int(match[1]))
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
        keys = list(dns_delay.keys())

        for k in keys:
            data['h'][server]['DNS'].append(handshake_delay['DNS'][k])
            data['h'][server]['Aeacus'].append(handshake_delay['Aeacus'][1000])
            data['mh'][server]['DNS'].append([d + ran_delay for d in handshake_delay['DNS'][k]])
            data['mh'][server]['Aeacus'].append(handshake_delay['Aeacus'][1000])
            data['mm1'][server]['DNS'].append([sum(x) for x in zip(dns_delay[k], handshake_delay['DNS'][k])])
            data['mm1'][server]['Aeacus'].append(handshake_delay['Aeacus'][1000])
            data['mm2'][server]['DNS'].append([sum(x) for x in zip(dns_delay[k], handshake_delay['DNS'][k])])
            data['mm2'][server]['Aeacus'].append(handshake_delay['Aeacus'][k])

    for k in data.keys():
        for d in ['DNS', 'Aeacus']:
            l = data[k][server][d]
            l_m = np.mean([np.median(x) for x in l])
            l_s = np.mean([np.std(x) for x in l])
            print(f'{k}, {server}, {d}, median: {l_m}, std: {l_s}')


def main():
    analyse('edge')
    analyse('cloud')


if __name__ == '__main__':
    main()
