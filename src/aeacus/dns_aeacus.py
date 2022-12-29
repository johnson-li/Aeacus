import argparse
import os.path
import socket
import struct
import time

from aeacus import TMP_SECRETS_PATH
from aioquic._buffer import Buffer
from aioquic.h0.connection import H0_ALPN
from aioquic.h3.connection import H3_ALPN
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection
from aioquic.quic.packet import pull_quic_header
from dnslib import DNSRecord, DNSQuestion
from aeacus.dns import resolver

BUFFER_SIZE = 102400


def parse_args():
    parser = argparse.ArgumentParser(description="QUIC server")
    parser.add_argument(
        "--nic-ingress",
        type=str,
        default="lo",
        help="listen on the specified address (defaults to ::)",
    )
    parser.add_argument(
        "--nic-egress",
        type=str,
        default="lo",
        help="listen on the specified address (defaults to ::)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8433,
        help="listen on the specified port (defaults to 8433)",
    )
    return parser.parse_args()


def init_socket(args):
    ingress_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
    ingress_socket.bind((args.nic_ingress, 0x0800))
    egress_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
    egress_socket.bind((args.nic_egress, 0x0800))
    return ingress_socket, egress_socket


def init_quic(args):
    configuration = QuicConfiguration(
        alpn_protocols=H3_ALPN + H0_ALPN + ["siduck"],
        is_client=False,
        max_datagram_frame_size=65536,
    )
    configuration.load_cert_chain(os.path.join(TMP_SECRETS_PATH, "cert.pem"), os.path.join(TMP_SECRETS_PATH, "key.pem"))
    return configuration


def handle_udp_msg(msg, addr, config, args):
    buf = Buffer(data=msg)
    header = pull_quic_header(
        buf, host_cid_length=config.connection_id_length
    )
    connection = QuicConnection(
        configuration=config,
        original_destination_connection_id=header.destination_cid,
    )
    connection.receive_datagram(msg, addr, time.time())
    server_name = connection.tls._client_hello_server_name
    print(f"Received a QUIC packet, server name: {server_name}")
    return server_name


def get_ip_str(data):
    return '.'.join(map(str, data))


def parse_ip_str(data: str):
    return struct.pack('!4s', b''.join([int(d).to_bytes(1, 'big') for d in data.split('.')]))


def serve(ingress_socket, egress_socket, config, args):
    while True:
        try:
            msg, addr = ingress_socket.recvfrom(BUFFER_SIZE)
            ip_header = struct.unpack('!BBHHHBBH4s4s', msg[14:34])
            ip_protocol = ip_header[6]
            if ip_protocol == 17:
                udp_header = struct.unpack('!HHHH', msg[34:42])
                dest_port = udp_header[1]
                if dest_port == args.port:
                    data = msg[42:]
                    try:
                        server_name = handle_udp_msg(data, addr, config, args)
                        ip_addr = resolver.resolve_name(server_name)[0]
                        # src_ip_addr = parse_ip_str("195.148.127.234")
                        print(f'Forward QUIC packet to {ip_addr}')
                        ip_bytes = parse_ip_str(ip_addr)
                        msg_new = b''.join([msg[:30], ip_bytes, msg[34:]])
                        egress_socket.send(msg_new)
                    except Exception as e:
                        print(e)
        except BlockingIOError as e:
            pass


def main():
    args = parse_args()
    ingress_socket, egress_socket = init_socket(args)
    config = init_quic(args)
    serve(ingress_socket, egress_socket, config, args)


if __name__ == '__main__':
    main()
