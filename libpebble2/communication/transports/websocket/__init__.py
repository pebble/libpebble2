from __future__ import absolute_import

__author__ = 'katharine'

import socket
import struct
import websocket

from .. import BaseTransport, MessageTarget, MessageTargetWatch
from .protocol import WebSocketRelayToWatch, WebSocketRelayFromWatch, endpoints, from_watch
from libpebble2.exceptions import ConnectionError, PebbleError


class MessageTargetPhone(MessageTarget):
    """
    Indicates that the message is directed at a connected phone running the Pebble mobile app. For this purpose,
    `pypkjs <https://github.com/pebble/pypkjs>`_ counts as a phone.
    """
    pass


class WebsocketTransport(BaseTransport):
    """
    Represents a connection via WebSocket to a phone running the Pebble mobile app, which is in turn connected
    to a Pebble over Bluetooth.

    :param url: The WebSocket URL to connect to, in standard format (e.g. ``ws://localhost:9000/``)
    """
    must_initialise = False

    def __init__(self, url):
        self.url = url
        """:type: str"""
        self.ws = None
        """:type: websocket.WebSocket"""

    def connect(self):
        try:
            self.ws = websocket.create_connection(self.url)
        except (websocket.WebSocketException, socket.error) as e:
            raise ConnectionError(str(e))

    @property
    def connected(self):
        return self.ws is not None and self.ws.connected

    def send_packet(self, message, target=MessageTargetWatch()):
        handlers = {
            MessageTargetWatch: self._send_to_watch,
            MessageTargetPhone: self._send_to_phone,
        }

        handlers[type(target)](message)

    def _send_to_watch(self, message):
        self.send_packet(WebSocketRelayToWatch(payload=message), target=MessageTargetPhone())

    def _send_to_phone(self, message):
        message = struct.pack('B', endpoints[type(message)]) + message.serialise()
        self.ws.send_binary(message)

    def read_packet(self):
        opcode, message = self.ws.recv_data()
        if opcode == websocket.ABNF.OPCODE_BINARY:
            endpoint, = struct.unpack_from('B', message, 0)
            if from_watch.get(endpoint, None) == WebSocketRelayFromWatch:
                return MessageTargetWatch(), message[1:]
            else:
                packet, length = from_watch[endpoint].parse(message[1:])
                return MessageTargetPhone(), packet
        elif opcode == websocket.ABNF.OPCODE_CLOSE:
            raise ConnectionError("Connection gracefully closed by peer.")
        else:
            raise PebbleError("Got unexpected WebSocket opcode {}".format(opcode))
