import argparse
import ipaddress
import ssl
import socket
import time
from urllib.parse import urlparse

from aioquic.h3.connection import H3_ALPN
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection
from aioquic.quic.logger import QuicFileLogger
from aioquic.tls import SessionTicket


def parse_args():
    parser = argparse.ArgumentParser(description="QUIC client")
    parser.add_argument(
        "--ca-certs", type=str, help="load CA certificates from the specified file"
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
        try:
            with open(args.session_ticket, "rb") as fp:
                configuration.session_ticket = pickle.load(fp)
        except FileNotFoundError:
            pass
    return configuration


def init_socket(args):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.connect(("localhost", 4433))
    return client_socket


def save_session_ticket(ticket: SessionTicket) -> None:
    """
    Callback which is invoked by the TLS engine when a new session ticket
    is received.
    """
    print("New session ticket received")
    pass
    # if args.session_ticket:
    #     with open(args.session_ticket, "wb") as fp:
    #         pickle.dump(ticket, fp)


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
    addr = infos[0][4]
    print(infos)
    config.server_name = server_name
    connection = QuicConnection(configuration=config, session_ticket_handler=save_session_ticket)
    connection.connect(addr, time.time())


def main():
    args = parse_args()
    client_socket = init_socket(args)
    config = init_quic(args)
    connect(client_socket, config, args)


if __name__ == '__main__':
    main()
