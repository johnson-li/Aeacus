import argparse
import json
import os.path
import socket
import time
from urllib.parse import urlparse

from aeacus import RESULTS_PATH, RESOURCE_PATH
from aioquic.h3.connection import H3_ALPN
from aioquic.quic import events
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection


def parse_args():
    parser = argparse.ArgumentParser(description="Test Alexa top 500 sites on QUIC support")
    return parser.parse_args()


def init_quic(args):
    configuration = QuicConfiguration(
        is_client=True, alpn_protocols=H3_ALPN
    )
    return configuration


def init_socket():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setblocking(0)
    return client_socket


def connect(config, domain):
    url = f'https://{domain}'
    parsed = urlparse(url)
    host = parsed.hostname
    port = 443
    server_name = host
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_DGRAM)
    for info in infos:
        if info[0] == socket.AF_INET:
            addr = info[4]
            config.server_name = server_name
            # config.server_name = "mobix.xuebing.me"
            conn = QuicConnection(configuration=config)
            conn.connect(addr, time.time())
            return conn


def log(s):
    print(f'{s}')


def listen(client_socket, conn: QuicConnection, result, domain):
    start_ts = time.time()
    while not conn._close_event and time.time() - start_ts < 3:
        for data, addr in conn.datagrams_to_send(time.time()):
            log(f'Sent {len(data)} bytes')
            client_socket.sendto(data, addr)
        try:
            msg, addr = client_socket.recvfrom(102400)
            log(f'Received {len(msg)} bytes')
            conn.receive_datagram(msg, addr, time.time())
            handle_quic_events(conn, result, domain)
        except BlockingIOError as e:
            pass
        except Exception as e:
            print(e)
    for data, addr in conn.datagrams_to_send(time.time()):
        log(f'Sent {len(data)} bytes')
        client_socket.sendto(data, addr)
    if domain not in result:
        log(f'[{domain}] QUIC not supported or handshake failed')
        result[domain] = -1


def handle_quic_events(conn: QuicConnection, result, domain):
    event = conn.next_event()
    while event is not None:
        log(f'[{domain}] QUIC supported ({type(event)})')
        if result.get(domain, 0) != 2:
            result[domain] = 1
        if isinstance(event, events.HandshakeCompleted):
            log(f'[{domain}] Handshake completed')
            result[domain] = 2
            stream_id = conn.get_next_available_stream_id()
            conn.send_stream_data(stream_id, "asdf".encode(), end_stream=True)
        if isinstance(event, events.StreamDataReceived):
            conn.close()
        event = conn.next_event()


def test_domain(domain, args, result):
    log(f'Testing {domain}')
    client_socket = init_socket()
    config = init_quic(args)
    conn = connect(config, domain)
    listen(client_socket, conn, result, domain)


def test_support():
    domains = open(os.path.join(RESOURCE_PATH, "alexa_top_500.txt")).readlines()
    domains = [d.strip() for d in domains]
    args = parse_args()
    result = {}
    for domain in domains:
        try:
            test_domain(domain, args, result)
        except Exception as e:
            print(e)
    with open(os.path.join(RESULTS_PATH, 'quic_support.json'), 'w+') as f:
        json.dump(result, f)


def verify_support():
    result = {}
    args = parse_args()
    data = json.load(open(os.path.join(RESULTS_PATH, "quic_support.json")))
    domains = [k for k, v in data.items() if v == 2]
    domains = list(sorted(domains))
    print(len(domains))
    for domain in domains:
        try:
            test_domain(domain, args, result)
        except Exception as e:
            print(e)
        input('Press enter to continue')


def analysis():
    with open(os.path.join(RESULTS_PATH, 'quic_support.json')) as f:
        data = json.load(f)
        print(len(data))
        res = [d for d in data.values()]
        res = [r for r in res if r == 1]
        print(len(res))
        # print([(k, v) for k, v in data.items() if v == 1])


if __name__ == '__main__':
    # test_support()
    # analysis()
    verify_support()
