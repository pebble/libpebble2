from __future__ import absolute_import
__author__ = 'katharine'

import socket

from .. import BaseTransport, MessageTarget, MessageTargetWatch
from .protocol import QemuPacket, QemuSPP, QemuRawPacket, HEADER_SIGNATURE, FOOTER_SIGNATURE
from libpebble2.exceptions import ConnectionError
from libpebble2.protocol.base.types import PacketDecodeError


class QemuMessageTarget(MessageTarget):
    def __init__(self, protocol=None, raw=False):
        self.protocol = protocol
        self.raw = raw


class QemuTransport(BaseTransport):
    BUFFER_SIZE = 2048
    must_initialise = True

    def __init__(self, host='127.0.0.1', port=12344, timeout=1, connect_timeout=5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.connect_timeout = connect_timeout
        self.socket = None
        self.assembled_data = bytes()
        self._connected = False

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
        except socket.error as e:
            raise ConnectionError(str(e))
        self._connected = True

    @property
    def connected(self):
        return self.socket is not None and self._connected

    def read_packet(self):
        while True:
            try:
                self.assembled_data += self.socket.recv(self.BUFFER_SIZE)
            except socket.error:
                self._connected = False
                raise ConnectionError("Disconnected.")
            try:
                packet, length = QemuPacket.parse(self.assembled_data)
            except PacketDecodeError:
                continue
            else:
                self.assembled_data = self.assembled_data[length:]
                if packet.signature == HEADER_SIGNATURE and packet.footer == FOOTER_SIGNATURE:
                    if isinstance(packet.data, QemuSPP):
                        return MessageTargetWatch(), packet.data.payload.tostring()
                    else:
                        return QemuMessageTarget(packet.protocol), packet.data
                else:
                    raise PacketDecodeError("QemuTransport: signature mismatch ({:x} = {:x}, {:x} = {:x})".format(
                        packet.signature,
                        HEADER_SIGNATURE,
                        packet.footer,
                        FOOTER_SIGNATURE,
                    ))

    def send_packet(self, message, target=MessageTargetWatch()):
        try:
            if isinstance(target, MessageTargetWatch):
                self.socket.send(QemuPacket(data=QemuSPP(payload=message)).serialise())
            elif isinstance(target, QemuMessageTarget):
                if not target.raw:
                    self.socket.send(QemuPacket(data=message).serialise())
                else:
                    self.socket.send(QemuRawPacket(protocol=target.protocol, data=message))
            else:
                assert False
        except socket.error as e:
            self._connected = False
            raise ConnectionError(str(e))
