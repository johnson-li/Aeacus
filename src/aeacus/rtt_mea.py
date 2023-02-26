import argparse
import socket
import time

from aeacus.echo_server import UDP_PORT

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--server', default='195.148.127.234')
args = parser.parse_args()
SERVER = args.server


def main():
    dns_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    dns_socket.setblocking(False)
    last_send_ts = 0
    interval = .1
    while True:
        ts = time.time()
        if ts - last_send_ts > interval:
            ts_str = str(int(1000 * ts))
            print(f'[{ts_str}] Send RTT query')
            dns_socket.sendto(ts_str.encode(), (SERVER, UDP_PORT))
            last_send_ts = time.time()
        try:
            msg, addr = dns_socket.recvfrom(1500)
            send_ts = float(msg.decode())
            print(f'[{send_ts}] Receive RTT response, delay: {ts * 1000 - send_ts} ms')
        except Exception:
            pass


if __name__ == '__main__':
    main()
