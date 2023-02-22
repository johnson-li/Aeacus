import socket
import time
from multiprocessing import Process

from dnslib import DNSRecord, EDNS0, EDNSOption

from aeacus.fake_server import DNS_PORT, UDP_PORT

SERVER_HOST = 'localhost'
TIMEOUT = 3

DOMAIN = 'edge.aeacus.xuebing.me'
# DOMAIN = 'cloud.aeacus.xuebing.me'

UDP_DATA = ('1' * 1200).encode()


def dns_sender():
    uuid = str(int(time.time() * 1000))
    dns_question = DNSRecord.question(f"{uuid}.{DOMAIN}", "A")
    dns_question.add_ar(
        EDNS0(udp_len=1200, opts=[EDNSOption(12, ('0' * (1200 - 15 - len(dns_question.pack()))).encode())]))
    dns_data = dns_question.pack()
    pass


def main():
    dns_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    dns_socket.setblocking(False)
    udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    udp_socket.setblocking(False)
    success = False
    for i in range(3):
        start_ts = time.time()
        udp_socket.sendto(UDP_DATA, (SERVER_HOST, UDP_PORT))
        while not success and time.time() - start_ts < .1:
            try:
                msg, addr = udp_socket.recvfrom(1200)
                if msg.decode() == '0':
                    success = True
                    print(f'UDP connection established')
            except Exception:
                pass
        if success:
            break
    if not success:
        print(f'Failed to connect to the server')
        return

    p = Process(target=dns_sender)
    p.start()
    while True:
        try:
            msg, addr = udp_socket.recvfrom(1200)
            if len(msg) == 1200:
                data = msg.decode()
                uuid = data[:data.find('!')]
                delay = time.time() - int(uuid) / 1000
                print(f'[{uuid}] Query succeeded, delay: {delay * 1000:.02f} ms')
        except Exception:
            pass


def run():
    if not success:
        return -2
    delay = -1
    for i in range(3):
        start_ts = time.time()
        dns_socket.sendto(dns_data, (SERVER_HOST, DNS_PORT))
        success = False
        if not success:
            return -1
    return delay


def main():
    dl = run()
    print(f'Aeacus handshake delay: {dl * 1000: .02f} ms')


if __name__ == '__main__':
    ts = time.time()
    for i in range(10):
        main()
        t = 1 - (time.time() - ts)
        if t > 0:
            time.sleep(t)
