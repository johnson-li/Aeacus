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

BUFFER_SIZE = 102400


def parse_args():
    parser = argparse.ArgumentParser(description="QUIC server")
    parser.add_argument(
        "-n",
        "--nic",
        type=str,
        default="lo",
        help="listen on the specified address (defaults to ::)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=4433,
        help="listen on the specified port (defaults to 4433)",
    )
    return parser.parse_args()


def init_socket(args):
    server_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
    server_socket.bind((args.nic, 0x0800))
    return server_socket


def init_quic(args):
    configuration = QuicConfiguration(
        alpn_protocols=H3_ALPN + H0_ALPN + ["siduck"],
        is_client=False,
        max_datagram_frame_size=65536,
    )
    configuration.load_cert_chain(os.path.join(TMP_SECRETS_PATH, "cert.pem"), os.path.join(TMP_SECRETS_PATH, "key.pem"))
    return configuration


def handle_udp_msg(server_socket, msg, addr, config, args):
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
    print(f"Server name: {server_name}")


def serve(server_socket, config, args):
    while True:
        try:
            msg, addr = server_socket.recvfrom(BUFFER_SIZE)
            ip_header = struct.unpack('!BBHHHBBH4s4s', msg[14:34])
            ip_protocol = ip_header[6]
            if ip_protocol == 17:
                udp_header = struct.unpack('!HHHH', msg[34:42])
                dest_port = udp_header[1]
                if dest_port == args.port:
                    data = msg[42:]
                    try:
                        handle_udp_msg(server_socket, data, addr, config, args)
                    except Exception as e:
                        print(e)
        except BlockingIOError as e:
            pass


def main():
    args = parse_args()
    server_socket = init_socket(args)
    config = init_quic(args)
    serve(server_socket, config, args)


if __name__ == '__main__':
    main()
