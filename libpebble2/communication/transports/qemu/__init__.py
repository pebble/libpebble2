from __future__ import absolute_import
__author__ = 'katharine'

import socket

from .. import BaseTransport, MessageTarget, MessageTargetWatch
from .protocol import QemuPacket, QemuInboundPacket, QemuSPP, QemuRawPacket, HEADER_SIGNATURE, FOOTER_SIGNATURE
from libpebble2.exceptions import ConnectionError
from libpebble2.protocol.base.types import PacketDecodeError


class MessageTargetQemu(MessageTarget):
    """
    Indicates that a message is directed at QEMU, rather than the firmware running on it. If ``raw`` is ``True``,
    the message should be a binary message (without framing), with QEMU protocol indicated by ``protocol``.
    Otherwise, the message should be a :class:`.PebblePacket` from :mod:`.protocol`.

    :param protocol: The protocol to send to, if sending a ``raw`` message
    :type protocol: :any:`int`
    :param raw: If ``True``, the message is pre-serialised and will be sent as-is after adding framing.
    :type raw: :any:`bool`
    """
    def __init__(self, protocol=None, raw=False):
        self.protocol = protocol
        self.raw = raw


class QemuTransport(BaseTransport):
    """
    Represents a connection to a `Pebble QEMU <https://github.com/pebble/qemu>`_ instance.

    :param host: The host on which the QEMU instance is running.
    :type host: str
    :param port: The port on which the QEMU instance has exposed its Pebble QEMU Protocol port.
    :type port: int
    """
    #: Number of bytes read from the socket at a time.
    BUFFER_SIZE = 2048
    must_initialise = True

    def __init__(self, host='127.0.0.1', port=12344):
        self.host = host
        self.port = port
        self.socket = None
        self.assembled_data = b''
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
            if len(self.assembled_data) > 0:
                try:
                    packet, length = QemuInboundPacket.parse(self.assembled_data)
                except PacketDecodeError:
                    pass
                else:
                    self.assembled_data = self.assembled_data[length:]
                    if packet.signature == HEADER_SIGNATURE and packet.footer == FOOTER_SIGNATURE:
                        if isinstance(packet.data, QemuSPP):
                            return MessageTargetWatch(), packet.data.payload
                        else:
                            return MessageTargetQemu(packet.protocol), packet.data
                    else:
                        raise PacketDecodeError("QemuTransport: signature mismatch ({:x} = {:x}, {:x} = {:x})".format(
                            packet.signature,
                            HEADER_SIGNATURE,
                            packet.footer,
                            FOOTER_SIGNATURE,
                        ))
            try:
                received = self.socket.recv(self.BUFFER_SIZE)
                if len(received) == 0:
                    self._connected = False
                    raise ConnectionError("Disconnected.")
                self.assembled_data += received
            except socket.error:
                self._connected = False
                raise ConnectionError("Disconnected.")

    def send_packet(self, message, target=MessageTargetWatch()):
        try:
            if isinstance(target, MessageTargetWatch):
                start_idx = 0
                bytes_left = len(message)
                while bytes_left:
                    bytes_to_send = bytes_left
                    if bytes_to_send > self.BUFFER_SIZE:
                        bytes_to_send = self.BUFFER_SIZE
                    chunk = message[start_idx:start_idx+bytes_to_send]
                    self.socket.send(QemuPacket(data=QemuSPP(payload=chunk)).serialise())
                    bytes_left -= bytes_to_send
                    start_idx += bytes_to_send
            elif isinstance(target, MessageTargetQemu):
                if not target.raw:
                    self.socket.send(QemuPacket(data=message).serialise())
                else:
                    self.socket.send(QemuRawPacket(protocol=target.protocol, data=message).serialise())
            else:
                assert False
        except socket.error as e:
            self._connected = False
            raise ConnectionError(str(e))
