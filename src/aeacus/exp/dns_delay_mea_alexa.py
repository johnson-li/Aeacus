import argparse
import json
import os
import time
from typing import List
from icmplib import resolve, multiping
from icmplib.models import Host, ICMPRequest
from icmplib.sockets import ICMPv4Socket
import numpy as np

from aeacus import EXP_RESULTS_PATH


def get_ldns():
    for line in os.popen('( nmcli dev list || nmcli dev show ) 2>/dev/null | grep DNS').read().splitlines():
        line = line.strip()
        if line:
            return line.split(':')[-1].strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', type=int, default=3)
    parser.add_argument('--period', type=float, default=.5)
    args = parser.parse_args()
    ldns = get_ldns()
    print(f'ldns: {ldns}')
    addresses = [ldns] * 10
    num_requests = int(args.duration / args.period) + 1
    request_ts = np.zeros((len(addresses), num_requests))
    response_ts = np.zeros((len(addresses), num_requests))
    with ICMPv4Socket(None, True) as sock:
        sock._sock.setblocking(False)
        counter = 0
        start_ts = time.time()
        ts = 0
        while time.time() <= start_ts + args.duration:
            if time.time() >= start_ts + counter * args.period:
                for i, addr in enumerate(addresses):
                    request = ICMPRequest(
                        destination=addr,
                        id=i,
                        sequence=counter)
                    sock.send(request)
                    request_ts[i, counter] = time.time()
                counter += 1
            try:
                ts = time.time()
                response = sock._sock.recvfrom(1024)
                packet = response[0]
                source = response[1][0]
                reply = sock._parse_reply(
                    packet=packet,
                    source=source,
                    current_time=time.time())
                response_ts[reply.id, reply.sequence] = time.time()
            except Exception as e:
                pass
    print(f'Sent {counter} requests')
    for i, addr in enumerate(addresses):
        req = request_ts[i]
        res = response_ts[i]
        rtt = res - req
        rtt = rtt[res > 0]
        print(f'Address: {addr}, rtt: {rtt.mean() * 1000:.02f} ms')
        # print(f'Address: {addr}, rtt: {rtt * 1000}')
        # print(f'Address: {addr}, {(req - start_ts) * 1000}')
        # print(f'Address: {addr}, {(res - start_ts) * 1000}')
    json.dump({
        'request_ts': request_ts.tolist(),
        'response_ts': response_ts.tolist(),
        'addresses': addresses,
        'duration': args.duration,
        'period': args.period,
        'ldns': ldns,
    }, open(os.path.join(EXP_RESULTS_PATH, 'dns_delay_mea_alexa.json'), 'w+'))
    


if __name__ == '__main__':
    main()
