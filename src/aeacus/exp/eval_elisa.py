import json
import os
import random
import subprocess
import time

from aeacus import RESOURCE_PATH, RESULTS_PATH


def eval_domain(domain, output_dir):
    ts = int(time.time() * 1000)
    print(f'[{ts}] Evaluating {domain}...')
    exe = os.path.expanduser('~/Workspace/Aeacus/bin/http3-client')
    with open(os.path.join(output_dir, f'{ts}_{domain}_dns.txt'), 'w+') as f1:
        with open(os.path.join(output_dir, f'{ts}_{domain}_aeacus.txt'), 'w+') as f2:
            p1 = subprocess.Popen([exe, f' https://{domain}'], stdout=f1, stderr=f1)
            p2 = subprocess.Popen([exe, f' https://{domain}', '195.148.127.234'], 
                                  stdout=f2, stderr=f2)
            p1.wait()
            p2.wait()


def eval():
    path = os.path.join(RESULTS_PATH, "quiche_support.json")
    quic_support = json.load(open(path))
    # quic_support = json.load(open(os.path.join(RESULTS_PATH, "quic_support.json")))
    output_dir = os.path.join(RESULTS_PATH, "eval_elisa")
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    domains = [k for k, v in quic_support.items() if v == 1]
    print(f'Num of supported sites: {len(domains)}')
    while True:
        domain = random.choice(domains)
        eval_domain(domain, output_dir)


def test_quic_support():
    domains = open(os.path.join(RESOURCE_PATH, "alexa_top_500.txt")).read().splitlines()
    path = os.path.join(RESULTS_PATH, "quiche_support.json")
    data = {}
    if os.path.exists(path):
        data = json.load(open(path))
    exe = os.path.expanduser('~/Workspace/Aeacus/bin/http3-client')
    print(f'Num of supported sites: {len([k for k, v in data.items() if v == 1])} / {len(data)}')
    for domain in domains:
        if data.get(domain, 0) in [1, -2]:
            continue
        p = subprocess.Popen([exe, '-u', f'https://{domain}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        success = 0
        _, err = p.communicate()
        log = err.decode()
        if 'handshake completed in' in log:
            success = 1
        elif 'Unable to resolve' in log:
            success = -1  # DNS lookup failed
        elif 'Send 1200 bytes to' in log:
            success = -2  # Data sent but no response
        data[domain] = success
        print(f'{domain}: {success}')
        json.dump(data, open(path, 'w+'))
        

def dump_test():
    path = os.path.join(RESULTS_PATH, "quiche_support.json")
    data = json.load(open(path))
    domains = [k for k, v in data.items() if v == 1]
    with open(os.path.join(RESULTS_PATH, "quiche_support.txt"), 'w+') as f:
        for domain in domains:
            f.write(f'{domain}\n')


if __name__ == '__main__':
    # eval()
    test_quic_support()
    # dump_test()
