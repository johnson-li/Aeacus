import argparse
import socket
import time
import traceback

from dnslib import DNSRecord, EDNS0, EDNSOption
from dnslib.dns import A

from aeacus.fake_server_dns import UDP_PORT

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--server', choices=['edge', 'cloud'], default='edge')
parser.add_argument('-t', '--timeout', type=int, default=-1)
args = parser.parse_args()
SERVER = args.server
TIMEOUT = args.timeout
RESOLVER_IP = "1.1.1.1"

DOMAIN = 'lab6.xuebing.me' if SERVER == 'edge' else 'gce.xuebing.me'
SERVER_HOST = '195.148.127.230' if SERVER == 'edge' else '34.118.22.129'
HANDSHAKE_INTERVAL = .3
NAME_LOOKUP_LOG = {}


def dns_query():
    dns_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    dns_socket.setblocking(False)
    uuid = str(int(time.time() * 1000))
    print(f'[{uuid}] DNS query sent', flush=True)
    dns_question = DNSRecord.question(f"{DOMAIN}", "A")
    dns_data = dns_question.pack()
    dns_socket.sendto(dns_data, (RESOLVER_IP, 53))
    time.sleep(HANDSHAKE_INTERVAL)
    ts = time.time()
    while time.time() - ts < 3:
        try:
            msg, addr = dns_socket.recvfrom(1500)
            dns_response = DNSRecord.parse(msg)
            ip = dns_response.rr[0].rdata
            return ip
        except Exception:
            pass
    return None


def main():
    dns_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    dns_socket.setblocking(False)
    udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    udp_socket.setblocking(False)
    start_ts = time.time()
    ts = time.time()
    dns_id = 0
    while TIMEOUT < 0 or time.time() < ts + TIMEOUT:
        if time.time() - start_ts > HANDSHAKE_INTERVAL:
            uuid = str(int(time.time() * 1000))
            print(f'[{uuid}] DNS query sent', flush=True)
            dns_question = DNSRecord.question(f"{DOMAIN}", "A")
            dns_question.header.id = dns_id
            dns_id = (dns_id + 1) % 65535
            dns_data = dns_question.pack()
            dns_socket.sendto(dns_data, (RESOLVER_IP, 53))
            start_ts = time.time()
            NAME_LOOKUP_LOG[dns_question.header.id] = uuid
        try:
            msg, addr = dns_socket.recvfrom(1500)
            dns_response = DNSRecord.parse(msg)
            uuid = NAME_LOOKUP_LOG[dns_response.header.id]
            query_ts = int(uuid) / 1000
            print(f'[{uuid}] DNS respond received, delay: {(time.time() - query_ts) * 1000:.02f} ms', flush=True)
            ip: A = dns_response.rr[0].rdata
            udp_socket.sendto((uuid + '!' * (1200 - len(uuid))).encode(), (str(ip), UDP_PORT))
        except BlockingIOError:
            pass
        except Exception as e:
            print(e)
            traceback.print_exc()
        try:
            msg, addr = udp_socket.recvfrom(1500)
            if len(msg) == 1200:
                data = msg.decode()
                uuid = data[:data.find('!')]
                query_ts = int(uuid) / 1000
                print(f'[{uuid}] Handshake succeeded, delay: {(time.time() - query_ts) * 1000:.02f} ms', flush=True)
        except BlockingIOError:
            pass
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
