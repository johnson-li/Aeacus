import ipaddress
import ssl
import socket
import time
from urllib.parse import urlparse

from aioquic.h3.connection import H3_ALPN
from aioquic.quic import events
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection
from aioquic.tls import SessionTicket

BUFFER_SIZE = 102400
CLOSE = False
DURATION = 2
SESSION_TICKET = None
START_TS = 0


def init_quic():
    configuration = QuicConfiguration(
        is_client=True, alpn_protocols=H3_ALPN
    )
    configuration.verify_mode = ssl.CERT_NONE
    configuration.session_ticket = SESSION_TICKET
    return configuration


def init_socket():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setblocking(0)
    return client_socket


def log(msg):
    print(f'[{time.time() - START_TS:.03f}] {msg}')


def save_session_ticket(ticket: SessionTicket) -> None:
    """
    Callback which is invoked by the TLS engine when a new session ticket
    is received.
    """
    ticket_id = {"".join("{:02x}".format(x) for x in ticket.ticket)}
    log(f'Add ticket: 0x{ticket_id}')
    global SESSION_TICKET
    SESSION_TICKET = ticket


def connect(config, rnd):
    url = "https://mobix.xuebing.online:4433"
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port
    try:
        ipaddress.ip_address(host)
        server_name = None
    except ValueError:
        server_name = host
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_DGRAM)
    for info in infos:
        if info[0] == socket.AF_INET:
            addr = ("34.118.22.129", 4433) if rnd == 1 else ("195.148.127.230", 4433)
            config.server_name = server_name
            conn = QuicConnection(configuration=config, session_ticket_handler=save_session_ticket)
            conn.connect(addr, time.time())
            break
    return conn


def handle_quic_events(conn: QuicConnection):
    event = conn.next_event()
    while event is not None:
        # log(f'Received event: {type(event)}')
        if isinstance(event, events.HandshakeCompleted):
            log(f'Early data accepted: {event.early_data_accepted}')
        elif isinstance(event, events.StreamDataReceived):
            log(f'Receive stream {event.stream_id}')
        event = conn.next_event()


def send_query(conn: QuicConnection):
    stream_id = conn.get_next_available_stream_id()
    conn.send_stream_data(stream_id, "".encode(), end_stream=True)
    log(f'Send stream {stream_id}')


def listen(client_socket, conn, init_start_ts=False):
    global START_TS
    if init_start_ts:
        START_TS = time.time()
    index = 0
    interval = .1
    while time.time() - START_TS < DURATION:
        for data, addr in conn.datagrams_to_send(time.time()):
            log(f'Send data: {len(data)} bytes to {addr}')
            client_socket.sendto(data, addr)
        if time.time() - START_TS > index * interval:
            index += 1
            send_query(conn)
        try:
            msg, addr = client_socket.recvfrom(BUFFER_SIZE)
            # log(f'Received {len(msg)} bytes')
            conn.receive_datagram(msg, addr, time.time())
            handle_quic_events(conn)
        except BlockingIOError as e:
            pass


def run(rnd):
    client_socket = init_socket()
    config = init_quic()
    conn = connect(config, rnd)
    listen(client_socket, conn, rnd == 1)
    client_socket.close()


def benchmark_aeacus():
    print(f'Test Aeacus')
    run(1)
    log('Start migration')
    global DURATION
    DURATION = 2 * DURATION
    run(2)


def benchmark_dns():
    print(f'Test DNS')
    run(1)
    global DURATION
    DURATION = 2 * DURATION
    run(2)


def main():
    benchmark_aeacus()
    global SESSION_TICKET
    SESSION_TICKET = None
    # benchmark_dns()


if __name__ == '__main__':
    main()
