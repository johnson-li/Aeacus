import argparse
import os.path
import pickle
import socket
import time
import threading
from typing import Dict, Optional

from paho.mqtt.client import MQTTMessage

from aeacus import DEMO_SECRETS_PATH
from aioquic._buffer import Buffer
from aioquic.h0.connection import H0_ALPN
from aioquic.h3.connection import H3_ALPN
from aioquic.quic import events
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection
from aioquic.quic.logger import QuicFileLogger
from aioquic.quic.packet import pull_quic_header, encode_quic_version_negotiation, PACKET_TYPE_INITIAL, \
    encode_quic_retry
from aioquic.quic.retry import QuicRetryTokenHandler
from aioquic.tls import SessionTicket
from paho.mqtt import client as mqtt_client

BUFFER_SIZE = 102400
CONNECTIONS: Dict[bytes, QuicConnection] = {}
RETRY = QuicRetryTokenHandler()
MQTT_CLIENT = mqtt_client.Client()
MQTT_CLIENT.on_connect = lambda client, userdata, flags, rc: print("Connected to the MQTT server")
MQTT_CLIENT.connect("mobix.xuebing.me")


class SessionTicketStore:
    """
    Simple in-memory store for session tickets.
    """

    def __init__(self) -> None:
        self.tickets: Dict[bytes, SessionTicket] = {}
        self.load()

    def add(self, ticket: SessionTicket) -> None:
        def publish_ticket():
            MQTT_CLIENT.publish("aeacus", pickle.dumps(ticket))

        ticket_id = {"".join("{:02x}".format(x) for x in ticket.ticket)}
        print(f'[From local] Add ticket: 0x{ticket_id}')
        self.tickets[ticket.ticket] = ticket
        threading.Thread(target=publish_ticket).start()

    def pop(self, label: bytes) -> Optional[SessionTicket]:
        res = self.tickets.pop(label, None)
        return res

    def load(self):
        def on_message(client, userdata, msg: MQTTMessage):
            ticket: SessionTicket = pickle.loads(msg.payload)
            if ticket.ticket not in self.tickets:
                ticket_id = {"".join("{:02x}".format(x) for x in ticket.ticket)}
                print(f'[From remote] Add ticket: 0x{ticket_id}')
                self.tickets[ticket.ticket] = ticket

        MQTT_CLIENT.subscribe("aeacus")
        MQTT_CLIENT.on_message = on_message


SESSION_TICKET_STORE = SessionTicketStore()


def parse_args():
    parser = argparse.ArgumentParser(description="QUIC server")
    parser.add_argument(
        "-c",
        "--certificate",
        type=str,
        default=os.path.join(DEMO_SECRETS_PATH, 'ssl_cert.pem'),
        help="load the TLS certificate from the specified file",
    )
    parser.add_argument(
        "--retry",
        action="store_true",
        help="send a retry for new connections",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="listen on the specified address (defaults to ::)",
    )
    parser.add_argument(
        "--mqtt",
        type=str,
        default="mobix.xuebing.me",
        help="The address of the MQTT server for sharing the session token",
    )
    parser.add_argument(
        "-k",
        "--private-key",
        type=str,
        default=os.path.join(DEMO_SECRETS_PATH, "ssl_key.pem"),
        help="load the TLS private key from the specified file",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=4433,
        help="listen on the specified port (defaults to 4433)",
    )
    parser.add_argument(
        "-l",
        "--secrets-log",
        type=str,
        help="log secrets to a file, for use with Wireshark",
    )
    parser.add_argument(
        "-q",
        "--quic-log",
        type=str,
        help="log QUIC events to QLOG files in the specified directory",
    )
    args = parser.parse_args()
    return args


def init_socket(args):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((args.host, args.port))
    return server_socket


def init_quic(args):
    if args.quic_log:
        quic_logger = QuicFileLogger(args.quic_log)
    else:
        quic_logger = None
    if args.secrets_log:
        secrets_log_file = open(args.secrets_log, "a")
    else:
        secrets_log_file = None
    configuration = QuicConfiguration(
        alpn_protocols=H3_ALPN + H0_ALPN + ["siduck"],
        is_client=False,
        max_datagram_frame_size=65536,
        quic_logger=quic_logger,
        secrets_log_file=secrets_log_file,
    )
    configuration.load_cert_chain(args.certificate, args.private_key)
    return configuration


def handle_stream_data_received(conn, event: events.StreamDataReceived):
    print(f'Stream data received, id: {event.stream_id}, data: {event.data.decode()}')
    conn.send_stream_data(event.stream_id, ("0123456789" * 50).encode(), end_stream=True)


def process_quic_events(conn: QuicConnection):
    event = conn.next_event()
    while event is not None:
        print(f'Received event: {type(event)}')
        if isinstance(event, events.ConnectionIdIssued):
            CONNECTIONS[event.connection_id] = conn
        elif isinstance(event, events.ConnectionIdRetired):
            assert CONNECTIONS[event.connection_id] == conn
            del CONNECTIONS[event.connection_id]
        elif isinstance(event, events.ConnectionTerminated):
            pass
        elif isinstance(event, events.HandshakeCompleted):
            pass
        elif isinstance(event, events.PingAcknowledged):
            pass
        elif isinstance(event, events.ConnectionTerminated):
            pass
        elif isinstance(event, events.StreamDataReceived):
            handle_stream_data_received(conn, event)
        event = conn.next_event()


def handle_udp_msg(server_socket, msg, addr, config, args):
    buf = Buffer(data=msg)
    try:
        header = pull_quic_header(
            buf, host_cid_length=config.connection_id_length
        )
    except ValueError:
        return
    if header.version is not None and header.version not in config.supported_versions:
        server_socket.sendto(encode_quic_version_negotiation(
            source_cid=header.destination_cid,
            destination_cid=header.source_cid,
            supported_versions=config.supported_versions,
        ), addr)
        return
    connection = CONNECTIONS.get(header.destination_cid, None)
    original_destination_connection_id: Optional[bytes] = None
    retry_source_connection_id: Optional[bytes] = None
    if connection is None and len(msg) >= 1200 and header.packet_type == PACKET_TYPE_INITIAL:
        if args.retry:
            if not header.token:
                # create a retry token
                source_cid = os.urandom(8)
                server_socket.sendto(
                    encode_quic_retry(
                        version=header.version,
                        source_cid=source_cid,
                        destination_cid=header.source_cid,
                        original_destination_cid=header.destination_cid,
                        retry_token=RETRY.create_token(
                            addr, header.destination_cid, source_cid
                        ),
                    ),
                    addr,
                )
                return
            else:
                try:
                    original_destination_connection_id, retry_source_connection_id = \
                        RETRY.validate_token(addr, header.token)
                except ValueError:
                    return
        else:
            original_destination_connection_id = header.destination_cid

        # create new connection
        connection = QuicConnection(
            configuration=config,
            original_destination_connection_id=original_destination_connection_id,
            retry_source_connection_id=retry_source_connection_id,
            session_ticket_fetcher=SESSION_TICKET_STORE.pop,
            session_ticket_handler=SESSION_TICKET_STORE.add,
        )
        CONNECTIONS[header.destination_cid] = connection
        CONNECTIONS[connection.host_cid] = connection
    if connection is not None:
        connection.receive_datagram(msg, addr, time.time())
        process_quic_events(connection)


def serve(server_socket, config, args):
    while True:
        try:
            msg, addr = server_socket.recvfrom(BUFFER_SIZE)
            handle_udp_msg(server_socket, msg, addr, config, args)
        except BlockingIOError as e:
            pass
        for conn in CONNECTIONS.values():
            for data, addr in conn.datagrams_to_send(time.time()):
                print(f'Send data: {len(data)} bytes')
                server_socket.sendto(data, addr)


def main():
    args = parse_args()
    server_socket = init_socket(args)
    config = init_quic(args)
    threading.Thread(target=lambda: serve(server_socket, config, args)).start()
    MQTT_CLIENT.loop_forever()


if __name__ == '__main__':
    main()
