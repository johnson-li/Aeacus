import socket
import time
from multiprocessing import Process

from dnslib import DNSRecord, EDNS0, EDNSOption

from aeacus.fake_server_aeacus import DNS_PORT, UDP_PORT

SERVER = 'edge'
# SERVER = 'cloud'
RESOLVER_IP = "1.1.1.1"

SERVER_HOST = '195.148.127.234' if SERVER == 'edge' else '34.118.22.129'
DOMAIN = 'exp.xuebing.me'
TIMEOUT = 3
CLIENT_ID = 1
UDP_DATA = f'C{CLIENT_ID}'.encode()
HANDSHAKE_INTERVAL = 1


def dns_sender():
    dns_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    dns_socket.setblocking(False)
    while True:
        uuid = str(int(time.time() * 1000))
        print(f'[{uuid}] DNS query sent')
        dns_question = DNSRecord.question(f"{CLIENT_ID}{uuid}.{DOMAIN}", "A")
        dns_question.add_ar(EDNS0(udp_len=1200))
        # dns_question.add_ar(
        #     EDNS0(udp_len=1200, opts=[EDNSOption(12, ('0' * (1200 - 15 - len(dns_question.pack()))).encode())]))
        dns_data = dns_question.pack()
        dns_socket.sendto(dns_data, (RESOLVER_IP, DNS_PORT))
        time.sleep(HANDSHAKE_INTERVAL)


def connect():
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
                    return udp_socket
            except BlockingIOError:
                pass
            except Exception as e:
                print(e)
        if success:
            break
    return None


def main():
    udp_socket = connect()
    if not udp_socket:
        print(f'Failed to connect to the server, abort')
        return

    p = Process(target=dns_sender)
    p.start()
    while True:
        try:
            msg, addr = udp_socket.recvfrom(1500)
            if len(msg) == 1200:
                data = msg.decode()
                uuid = data[:data.find('!')]
                delay = time.time() - int(uuid) / 1000
                print(f'[{uuid}] Handshake succeeded, delay: {delay * 1000:.02f} ms')
        except BlockingIOError:
            pass
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
