import argparse
import socket
import time

from aeacus.echo_server import UDP_PORT

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--server', default='195.148.127.234')
parser.add_argument('-t', '--timeout', type=int, default=-1)
args = parser.parse_args()
TIMEOUT = args.timeout
SERVER = args.server


def main():
    dns_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    dns_socket.setblocking(False)
    last_send_ts = 0
    interval = .1
    start_ts = time.time()
    while TIMEOUT < 0 or time.time() - start_ts < TIMEOUT:
        ts = time.time()
        if ts - last_send_ts > interval:
            ts_str = str(int(1000 * ts))
            print(f'[{ts_str}] Send RTT query', flush=True)
            dns_socket.sendto(ts_str.encode(), (SERVER, UDP_PORT))
            last_send_ts = time.time()
        try:
            msg, addr = dns_socket.recvfrom(1500)
            send_ts = int(msg.decode())
            print(f'[{send_ts}] Receive RTT response, delay: {ts * 1000 - send_ts} ms', flush=True)
        except Exception:
            pass


if __name__ == '__main__':
    main()
