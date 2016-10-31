#!/usr/bin/env python

import argparse
import logging
import os
import socket
import struct
import threading
import time


SOCKET_TTL = 20
SOCKET_TIMEOUT = 5
SOCKET_SEND_TIME = 1
SOCKET_MAXPRINT = 64
SOCKET_SPECIAL_HEADER = 'HELLO FROM'


class SimpleMulticastTestThread(threading.Thread):

    def __init__(self, stream_addr, stream_port, bind_addr=None, ttl=SOCKET_TTL):
        super(SimpleMulticastTestThread, self).__init__()

        self.stop_event = threading.Event()
        logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s', datefmt='%Y:%m:%d %H:%M:%S')

        self.stream_addr = stream_addr
        self.stream_port = stream_port
        self.bind_addr = bind_addr

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.settimeout(SOCKET_TIMEOUT)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP, 1)

    def stop(self):
        self.stop_event.set()
        self.join()

    @property
    def stopped(self):
        return self.stop_event.isSet()


class SimpleMulticastTestWriter(SimpleMulticastTestThread):

    def run(self):
        if self.bind_addr:
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(self.bind_addr))

        while not self.stopped:
            time.sleep(SOCKET_SEND_TIME)
            try:
                self.sock.sendto('{0!s} {1!s}'.format(SOCKET_SPECIAL_HEADER, socket.gethostname()), (self.stream_addr, self.stream_port))
            except:
                logging.exception("Error when trying to send data")


class SimpleMulticastTestReader(SimpleMulticastTestThread):

    def run(self):
        self.sock.bind(('', self.stream_port))

        if self.bind_addr:
            mcast_membership = socket.inet_aton(self.stream_addr) + socket.inet_aton(self.bind_addr)
        else:
            mcast_membership = struct.pack('4sL', socket.inet_aton(self.stream_addr), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mcast_membership)

        while not self.stopped:
            try:
                rdata = self.sock.recvfrom(0xffff)
                if len(rdata[0]) < SOCKET_MAXPRINT and rdata[0][:len(SOCKET_SPECIAL_HEADER)] == SOCKET_SPECIAL_HEADER:
                    rdataout = rdata[0]
                else:
                    rdataout = 'bytes: [{0!s}:...]'.format(':'.join('{:02x}'.format(ord(bt)) for bt in rdata[0][:10]))
                logging.info("Received packet from {0!s}:{1!s} with data {2!s}".format(rdata[1][0], rdata[1][1], rdataout))
            except socket.timeout:
                logging.debug("No data received")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple Multicast Test Tool")
    parser.add_argument('--group', type=str, required=True, help="Multicast group to join/send data")
    parser.add_argument('--port', type=int, required=True, help="Multicast group port to join/send data")
    parser.add_argument('--bind', type=str, required=False, default=None, help="Bind to IP address (not required)")
    parser.add_argument('--ttl', type=int, required=False, default=SOCKET_TTL, help="TTL for multicast packets")
    args = parser.parse_args()

    smtr = SimpleMulticastTestReader(args.group, args.port, args.bind, args.ttl)
    smtw = SimpleMulticastTestWriter(args.group, args.port, args.bind, args.ttl)
    smtr.start()
    smtw.start()
    try:
        while True:
            time.sleep(0xffff)
    except KeyboardInterrupt:
        logging.info("Stopping. Please wait.")
    finally:
        smtw.stop()
        smtr.stop()
