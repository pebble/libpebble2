from __future__ import absolute_import

__author__ = 'katharine'

import struct
import websocket

from .. import BaseTransport, MessageTarget, MessageTargetWatch
from .protocol import WebSocketRelayToWatch, WebSocketRelayFromWatch, endpoints, from_watch


class MessageTargetPhone(MessageTarget):
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def __repr__(self):
        return "%s(%d)" % (type(self).__name__, self.endpoint)


class WebsocketTransport(BaseTransport):
    must_initialise = False

    def __init__(self, url):
        self.url = url
        """:type: str"""
        self.ws = None
        """:type: websocket.WebSocket"""

    def connect(self):
        self.ws = websocket.create_connection(self.url)

    def send_packet(self, message, target=MessageTargetWatch()):
        handlers = {
            MessageTargetWatch: self._send_to_watch,
            MessageTargetPhone: self._send_to_phone,
        }

        handlers[type(target)](message, target)

    def _send_to_watch(self, message, target):
        self.send_packet(WebSocketRelayToWatch(payload=message).serialise(),
                         target=MessageTargetPhone(endpoints[WebSocketRelayToWatch]))

    def _send_to_phone(self, message, target):
        message = struct.pack('B', target.endpoint) + message.serialise()
        self.ws.send_binary(message)

    def read_packet(self):
        opcode, message = self.ws.recv_data()
        if opcode == websocket.ABNF.OPCODE_BINARY:
            endpoint, = struct.unpack_from('B', message, 0)
            if from_watch.get(endpoint, None) == WebSocketRelayFromWatch:
                return MessageTargetWatch(), message[1:]
            else:
                packet = from_watch[endpoint].parse(message[1:])
                return MessageTargetPhone(endpoint), packet
