from __future__ import absolute_import
__author__ = 'Liam McLoughlin'

import struct

try:
    from pebble import pulse2
except ImportError:
    pass

from . import BaseTransport, MessageTargetWatch
from libpebble2.exceptions import ConnectionError, PebbleError


class PULSETransport(BaseTransport):
    """
    Represents a direct connection to a physical/virtual Pebble uses the PULSEv2 interface.
    This transport expects to be given a PULSE2 Link object.

    :param connection: A PULSE2 Interface object to tunnel Pebble Protocol over.
    :type link: pulse2.link.Interface
    """
    must_initialise = True

    PPOPULSE_PORT = 0x3e22

    OPCODE_PROTOCOL_DATA = 0x1
    OPCODE_CONNECT = 0x2
    OPCODE_DISCONNECT = 0x3

    def __init__(self, link):
        self.link = link
        self.connection = None
        self.buffer = b''

        try:
            from pebble import pulse2
        except ImportError:
            raise PebbleError('pulse2 package not installed: it is required for PULSE transport')

    @staticmethod
    def _opcode(opcode):
        return struct.pack('B', opcode)

    @staticmethod
    def _chunks(list_items, chunk_length):
        for i in xrange(0, len(list_items), chunk_length):
            yield list_items[i:i+chunk_length]

    def connect(self):
        self.connection = self.link.open_socket('reliable', self.PPOPULSE_PORT)
        if not self.connection:
            raise ConnectionError('Failed to open PPoPULSE socket')

        self._send_with_opcode(self.OPCODE_CONNECT)

    def disconnect(self):
        if self.connected:
            try:
                self._send_with_opcode(self.OPCODE_DISCONNECT)
            except pulse2.exceptions.SocketClosed:
                pass
            self.connection.close()
            self.connection = None

    @property
    def connected(self):
        return self.connection is not None

    def read_packet(self):
        while self.connected:
            if len(self.buffer) >= 2:
                length, = struct.unpack('!H', self.buffer[:2])
                length += 4

                if len(self.buffer) >= length:
                    msg_data = self.buffer[:length]
                    self.buffer = self.buffer[length:]

                    return MessageTargetWatch(), msg_data

            try:
                packet = self.connection.receive(block=True)
            except (AttributeError, pulse2.exceptions.SocketClosed):
                self.connection = None
                raise ConnectionError('PULSE transport closed')

            assert packet[0] == self._opcode(self.OPCODE_PROTOCOL_DATA)
            self.buffer += packet[1:]

    def send_packet(self, message, target=MessageTargetWatch()):
        assert isinstance(target, MessageTargetWatch)
        for chunk in self._chunks(message, self.connection.mtu - 1):
            self._send_with_opcode(self.OPCODE_PROTOCOL_DATA, chunk)

    def _send_with_opcode(self, opcode, body=None):
        assert self.connected

        data = self._opcode(opcode)
        if body:
            data += body
        self.connection.send(data)
