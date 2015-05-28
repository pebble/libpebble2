from __future__ import absolute_import
__author__ = 'katharine'

import socket

from .. import BaseTransport, MessageTarget, MessageTargetWatch
from .protocol import QemuPacket, QemuSPP, HEADER_SIGNATURE, FOOTER_SIGNATURE
from protocol.base.types import PacketDecodeError


class QemuMessageTarget(MessageTarget):
    def __init__(self, protocol):
        self.protocol = protocol


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

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    def read_packet(self):
        while True:
            self.assembled_data += self.socket.recv(self.BUFFER_SIZE)
            try:
                packet, length = QemuPacket.parse(self.assembled_data)
            except PacketDecodeError as e:
                continue
            else:
                if packet.signature == HEADER_SIGNATURE and packet.footer == FOOTER_SIGNATURE:
                    self.assembled_data = self.assembled_data[length:]
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
        if isinstance(target, MessageTargetWatch):
            data = QemuSPP(payload=message)
        else:
            data = message
        packet = QemuPacket(data=data)
        self.socket.send(packet.serialise())
