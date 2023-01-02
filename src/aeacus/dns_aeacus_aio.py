import argparse
import asyncio
import os.path
import random
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
BENCHMARK = False


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
        default=4433,
        help="listen on the specified port (defaults to 4433)",
    )
    parser.add_argument(
        "--benchmark",
        action='store_true'
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


async def serve(ingress_socket, egress_socket, config, args):
    loop = asyncio.get_running_loop()
    while True:
        try:
            msg, addr = await loop.sock_recvfrom(ingress_socket, BUFFER_SIZE)
            mac_head = msg[:14]
            ip_head = msg[14:34]
            payload = msg[34:]
            print(f'Received {len(msg)} bytes from {addr}')
            ip_header = struct.unpack('!BBHHHBBH4s4s', msg[14:34])
            ip_protocol = ip_header[6]
            if ip_protocol == 17:
                udp_header = struct.unpack('!HHHH', msg[34:42])
                dest_port = udp_header[1]
                if dest_port == args.port:
                    data = msg[42:]
                    try:
                        server_name = handle_udp_msg(data, addr, config, args)
                        ip_addr = (await resolver.resolve_name_async(server_name))[0]
                        if BENCHMARK:
                            if random.randint(0, 1) > 0:
                                ip_addr = "192.168.58.15"
                            else:
                                ip_addr = "192.168.58.16"
                        print(f'Forward QUIC packet to {ip_addr}')
                        ip_dst_bytes = parse_ip_str(ip_addr)
                        ip_src_bytes = parse_ip_str("10.0.10.13")
                        mac_src_bytes = b'\x3a\x4d\xa7\x05\x2a\x13'
                        mac_dst_bytes = b'\x3a\x4d\xa7\x05\x2a\x12'
                        mac_bytes = b''.join([mac_dst_bytes, mac_src_bytes, msg[12:14]])
                        mac_bytes = mac_head
                        ip_bytes = b''.join([ip_head[:10], b'\x00\x00', ip_head[12:16], ip_dst_bytes])
                        check_sum = 0
                        for i in range(0, 20, 2):
                            check_sum += ip_bytes[i] << 8 | ip_bytes[i + 1]
                            if check_sum >= 0x10000:
                                check_sum %= 0x10000
                                check_sum += 1
                        check_sum ^= 0xFFFF
                        ip_bytes = b''.join([ip_bytes[:10], check_sum.to_bytes(2, "big"), ip_bytes[12:]])
                        payload = b''.join([payload[:6], b'\x00\x00', payload[8:]])
                        msg_new = b''.join([mac_bytes, ip_bytes, payload])
                        await loop.sock_sendall(egress_socket, msg_new)
                    except Exception as e:
                        print(e)
        except BlockingIOError as e:
            pass


async def main():
    args = parse_args()
    if args.benchmark:
        global BENCHMARK
        BENCHMARK = True
    loop = asyncio.get_running_loop()
    ingress_socket, egress_socket = init_socket(args)
    config = init_quic(args)
    await serve(ingress_socket, egress_socket, config, args)
    loop.run_forever()


if __name__ == '__main__':
    asyncio.run(main())
