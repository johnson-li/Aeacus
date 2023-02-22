import socket
import time

SERVER_HOST = 'localhost'
TIMEOUT = 5


def main():
    udp_data = ("0" * 1200).encode()
    dns_data = "".encode()
    udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    dns_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    start_ts = time.time()
    udp_socket.sendto(udp_data, (SERVER_HOST, 8083))
    dns_socket.sendto(dns_data, (SERVER_HOST, 53))
    while time.time() - start_ts < TIMEOUT:
        msg, addr = udp_socket.recvfrom(1200)
        print(addr)


if __name__ == '__main__':
    main()
