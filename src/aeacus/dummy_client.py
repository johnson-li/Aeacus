import argparse
import ipaddress
import os.path
import pickle
import ssl
import socket
import time
from urllib.parse import urlparse

from aeacus import DEMO_SECRETS_PATH
from aioquic.h3.connection import H3_ALPN
from aioquic.quic import events
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection
from aioquic.quic.logger import QuicFileLogger
from aioquic.tls import SessionTicket

BUFFER_SIZE = 102400
SESSION_TICKET_FILE = None
CLOSE = False


def parse_args():
    parser = argparse.ArgumentParser(description="QUIC client")
    parser.add_argument(
        "--ca-certs", type=str, default=os.path.join(DEMO_SECRETS_PATH, "pycacert.pem"),
        help="load CA certificates from the specified file"
    )
    parser.add_argument(
        "url", type=str, nargs="+", default="https://localhost:4433/",
        help="the URL to query (must be HTTPS)"
    )
    parser.add_argument(
        "-k",
        "--insecure",
        action="store_true",
        help="do not validate server certificate",
    )
    parser.add_argument(
        "-q",
        "--quic-log",
        type=str,
        help="log QUIC events to QLOG files in the specified directory",
    )
    parser.add_argument(
        "-l",
        "--secrets-log",
        type=str,
        help="log secrets to a file, for use with Wireshark",
    )
    parser.add_argument(
        "-s",
        "--session-ticket",
        type=str,
        help="read and write session ticket from the specified file",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="increase logging verbosity"
    )
    parser.add_argument(
        "--local-port",
        type=int,
        default=0,
        help="local port to bind for connections",
    )
    parser.add_argument(
        "--zero-rtt", action="store_true", help="try to send requests using 0-RTT"
    )
    return parser.parse_args()


def init_quic(args):
    configuration = QuicConfiguration(
        is_client=True, alpn_protocols=H3_ALPN
    )
    if args.ca_certs:
        configuration.load_verify_locations(args.ca_certs)
    if args.insecure:
        configuration.verify_mode = ssl.CERT_NONE
    if args.quic_log:
        configuration.quic_logger = QuicFileLogger(args.quic_log)
    if args.secrets_log:
        configuration.secrets_log_file = open(args.secrets_log, "a")
    if args.session_ticket:
        global SESSION_TICKET_FILE
        SESSION_TICKET_FILE = args.session_ticket
        try:
            with open(args.session_ticket, "rb") as fp:
                configuration.session_ticket = pickle.load(fp)
        except FileNotFoundError:
            pass
    return configuration


def init_socket(args):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setblocking(0)
    return client_socket


def save_session_ticket(ticket: SessionTicket) -> None:
    """
    Callback which is invoked by the TLS engine when a new session ticket
    is received.
    """
    if SESSION_TICKET_FILE:
        with open(SESSION_TICKET_FILE, "wb") as fp:
            pickle.dump(ticket, fp)


def connect(client_socket, config, args):
    url = args.url[0]
    parsed = urlparse(url)
    assert parsed.scheme in (
        "https",
        "wss",
    ), "Only https:// or wss:// URLs are supported."
    host = parsed.hostname
    if parsed.port is not None:
        port = parsed.port
    else:
        port = 443
    try:
        ipaddress.ip_address(host)
        server_name = None
    except ValueError:
        server_name = host
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_DGRAM)
    for info in infos:
        if info[0] == socket.AF_INET:
            addr = info[4]
            config.server_name = server_name
            conn = QuicConnection(configuration=config, session_ticket_handler=save_session_ticket)
            conn.connect(addr, time.time())
            break
    if args.zero_rtt:
        send_new_query_stream(conn)
    return conn


def send_new_query_stream(conn):
    stream_id = conn.get_next_available_stream_id()
    conn.send_stream_data(stream_id, "query".encode())


def on_stream_data_received(data):
    print(f'Stream data received: {len(data)} bytes')


def handle_quic_events(conn: QuicConnection):
    event = conn.next_event()
    while event is not None:
        print(f'Received event: {type(event)}')
        if isinstance(event, events.HandshakeCompleted):
            print(f'Early data accepted: {event.early_data_accepted}')
            send_new_query_stream(conn)
        elif isinstance(event, events.StreamDataReceived):
            on_stream_data_received(event.data.decode())
            if event.end_stream:
                conn.close()
                global CLOSE
                CLOSE = True

        event = conn.next_event()


def listen(client_socket, conn, args):
    while not CLOSE:
        try:
            msg, addr = client_socket.recvfrom(BUFFER_SIZE)
            print(f'Received {len(msg)} bytes')
            conn.receive_datagram(msg, addr, time.time())
            handle_quic_events(conn)
        except BlockingIOError as e:
            pass
        for data, addr in conn.datagrams_to_send(time.time()):
            print(f'Send data: {len(data)} bytes to {addr}')
            client_socket.sendto(data, addr)


def main():
    args = parse_args()
    client_socket = init_socket(args)
    config = init_quic(args)
    conn = connect(client_socket, config, args)
    listen(client_socket, conn, args)


if __name__ == '__main__':
    main()
