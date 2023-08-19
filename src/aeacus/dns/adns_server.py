import asyncio
import os
import socket
from dnslib import DNSRecord, DNSError, QTYPE, RCODE, RR, EDNS0, CLASS, DNSQuestion, EDNSOption, A, CNAME

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("195.148.127.234", 53))
    buf_size = 65535
    ip_path = '/tmp/server_ip.txt'
    while True:
        try:
            data, addr = s.recvfrom(buf_size)
            ip = '192.168.56.107'
            if os.path.exists(ip_path):
                with open('/tmp/server_ip.txt') as f:
                    i = f.read().strip()
                    if i:
                        ip = i
            request = DNSRecord.parse(data)
            q: DNSQuestion = request.questions[0]
            # Respond only to the 'A' record
            if q.qtype == 1:
                reply = request.reply(ra=1, aa=0)
                reply.add_answer(*RR.fromZone(f"{q.qname} A {ip}"))
                s.sendto(reply.pack(), addr)
        except Exception as e:
            print(e)

if __name__ == '__main__':
    main()
