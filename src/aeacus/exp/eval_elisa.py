import json
import os
import random
import subprocess
import time

from aeacus import RESOURCE_PATH, RESULTS_PATH


def eval_domain(domain, output_dir):
    print(f'Evaluating {domain}...')
    ts = int(time.time() * 1000)
    exe = os.path.expanduser('~/Workspace/Aeacus/bin/http3-client')
    with open(os.path.join(output_dir, f'{ts}_{domain}_dns.txt'), 'w+') as f1:
        with open(os.path.join(output_dir, f'{ts}_{domain}_aeacus.txt'), 'w+') as f2:
            p1 = subprocess.Popen([exe, f' https://{domain}'], stdout=f1, stderr=f1)
            p2 = subprocess.Popen([exe, f' https://{domain}', '195.148.127.234'], 
                                  stdout=f2, stderr=f2)
            p1.wait()
            p2.wait()


def eval():
    quic_support = json.load(open(os.path.join(RESULTS_PATH, "quic_support.json")))
    output_dir = os.path.join(RESULTS_PATH, "eval_elisa")
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    domains = [k for k, v in quic_support.items() if v == 2]
    while True:
        domain = random.choice(domains)
        eval_domain(domain, output_dir)


def test_quic_support():
    domains = open(os.path.join(RESOURCE_PATH, "alexa_top_500.txt")).read().splitlines()
    data = {}
    for domain in domains:
        exe = os.path.expanduser('~/Workspace/Aeacus/bin/http3-client')
        p = subprocess.Popen([exe, f' https://{domain}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        success = False
        _, err = p.communicate()
        log = err.decode()
        print(log)
        success = 'handshake completed' in log
        data[domain] = success
        print(f'{domain}: {success}')
    json.dump(data, open(os.path.join(RESULTS_PATH, "quiche_support.json"), 'w+'))
        

def test_quic_support0():
    result_path = os.path.join(RESULTS_PATH, "quiche_test")
    success_count = 0
    quic_error_count = 0
    program_error_count = 0
    for f in os.listdir(result_path):
        f = os.path.join(result_path, f)
        data = open(f).read()
        if 'handshake completed' in data:
            success_count += 1
        elif 'initial send failed: Done' in data:
            program_error_count += 1
            os.remove(f)
        else:
            quic_error_count += 1
    print(f'Success: {success_count}, Quic error: {quic_error_count}'
          f', Program error: {program_error_count}'
          f', total: {success_count + quic_error_count + program_error_count}')

if __name__ == '__main__':
    # eval()
    # test_quic_support()
    test_quic_support0()
