from __future__ import absolute_import

__author__ = 'katharine'

from enum import Enum
import struct

from .transports import BaseTransport, MessageTargetWatch
from libpebble2.events import BaseEventHandler
from libpebble2.protocol.base import PebblePacket
from libpebble2.protocol.system import (PhoneAppVersion, AppVersionResponse, WatchVersion, WatchVersionRequest,
                                        WatchModel, ModelRequest, Model)

_EventType = Enum('_EventType', ('Watch', 'Transport'))


class PebbleConnection(object):
    def __init__(self, transport, event_handler):
        """
        Low-level connection to a pebble; deals in terms of PebblePackets.
        :param transport: BaseTransport
        :param event_handler: BaseEventHandler
        """
        assert isinstance(transport, BaseTransport)
        assert issubclass(event_handler, BaseEventHandler)
        self.transport = transport
        self.event_handler = event_handler()
        self._register_internal_handlers()
        self._watch_info = None
        self._watch_model = None

    def connect(self):
        self.transport.connect()

    def pump_reader(self):
        origin, message = self.transport.read_packet()
        if isinstance(origin, MessageTargetWatch):
            self.handle_watch_message(message)
        else:
            self.broadcast_transport_message(origin, message)

    def handle_watch_message(self, message):
        while len(message) >= 4:
            packet, length = PebblePacket.parse_message(message)
            message = message[length:]
            self.event_handler.broadcast_event((_EventType.Watch, type(packet)), packet)
            if length == 0:
                break

    def broadcast_transport_message(self, origin, message):
        self.event_handler.broadcast_event((_EventType.Transport, type(origin), type(message)), message)

    def register_transport_endpoint(self, origin, message_type, handler):
        return self.event_handler.register_handler((_EventType.Transport, origin, message_type), handler)

    def register_endpoint(self, endpoint, handler):
        return self.event_handler.register_handler((_EventType.Watch, endpoint), handler)

    def unregister_endpoint(self, handle):
        return self.event_handler.unregister_handler(handle)

    def read_from_endpoint(self, endpoint):
        return self.event_handler.wait_for_event((_EventType.Watch, endpoint))

    def get_endpoint_queue(self, endpoint):
        return self.event_handler.queue_events((_EventType.Watch, endpoint))

    def read_transport_message(self, origin, message_type):
        return self.event_handler.wait_for_event((_EventType.Transport, origin, message_type))

    def send_packet(self, packet):
        serialised = packet.serialise_packet()
        self.transport.send_packet(serialised)

    def _register_internal_handlers(self):
        if self.transport.must_initialise:
            self.register_endpoint(PhoneAppVersion, self._app_version_response)

    def _app_version_response(self, packet):
        packet = PhoneAppVersion(message=AppVersionResponse(
            protocol_version=0xFFFFFFFF,
            session_caps=0x80000000,
            platform_flags=50,
            response_version=2,
            major_version=3,
            minor_version=0,
            bugfix_version=0,
            protocol_caps=0
        ))
        self.send_packet(packet)

    @property
    def watch_info(self):
        if self._watch_info is None:
            self.send_packet(WatchVersion(data=WatchVersionRequest()))
            self._watch_info = self.read_from_endpoint(WatchVersion).data
        return self._watch_info

    @property
    def watch_model(self):
        if self._watch_model is None:
            self.send_packet(WatchModel(data=ModelRequest()))
            info_bytes = self.read_from_endpoint(WatchModel).data.data
            if len(info_bytes) == 4:
                self._watch_model = struct.unpack('>I', info_bytes)
            else:
                self._watch_model = Model.Unknown
        return self._watch_model
