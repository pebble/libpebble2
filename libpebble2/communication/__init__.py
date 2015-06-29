from __future__ import absolute_import

__author__ = 'katharine'

from collections import namedtuple
from enum import Enum
import logging
import struct
import threading

from .transports import BaseTransport, MessageTargetWatch
from libpebble2.events.threaded import ThreadedEventHandler
from libpebble2.exceptions import PacketDecodeError
from libpebble2.protocol.base import PebblePacket
from libpebble2.protocol.system import (PhoneAppVersion, AppVersionResponse, WatchVersion, WatchVersionRequest,
                                        WatchModel, ModelRequest, Model)

logger = logging.getLogger("libpebble2.communication")

_EventType = Enum('_EventType', ('Watch', 'Transport'))

FirmwareVersion = namedtuple('FirmwareVersion', ('major', 'minor', 'patch', 'suffix'))


class PebbleConnection(object):
    def __init__(self, transport, log_protocol_level=None, log_packet_level=None):
        """
        Low-level connection to a pebble; deals in terms of PebblePackets.
        :param transport: BaseTransport
        """
        assert isinstance(transport, BaseTransport)
        self.transport = transport
        self.event_handler = ThreadedEventHandler()
        self._register_internal_handlers()
        self._watch_info = None
        self._watch_model = None
        self.log_protocol_level = log_protocol_level
        self.log_packet_level = log_packet_level

    def connect(self):
        self.transport.connect()

    @property
    def connected(self):
        return self.transport.connected

    def pump_reader(self):
        origin, message = self.transport.read_packet()
        if isinstance(origin, MessageTargetWatch):
            self.handle_watch_message(message)
        else:
            self.broadcast_transport_message(origin, message)

    def run_sync(self):
        while self.connected:
            try:
                self.pump_reader()
            except PacketDecodeError as e:
                logger.warning("Packet decode failed: %s", e)

    def run_async(self):
        thread = threading.Thread(target=self.run_sync)
        thread.daemon = True
        thread.name = "PebbleConnection"
        thread.start()

    def handle_watch_message(self, message):
        while len(message) >= 4:
            if self.log_protocol_level is not None:
                logger.log(self.log_protocol_level, "<- %s", message.encode('hex'))
            self.event_handler.broadcast_event("raw_inbound", message)
            packet, length = PebblePacket.parse_message(message)
            if self.log_packet_level is not None:
                logger.log(self.log_packet_level, "<- %s", packet)
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

    def register_raw_outbound_handler(self, handler):
        return self.event_handler.register_handler("raw_outbound", handler)

    def register_raw_inbound_handler(self, handler):
        return self.event_handler.register_handler("raw_inbound", handler)

    def unregister_endpoint(self, handle):
        return self.event_handler.unregister_handler(handle)

    def read_from_endpoint(self, endpoint):
        return self.event_handler.wait_for_event((_EventType.Watch, endpoint))

    def get_endpoint_queue(self, endpoint):
        return self.event_handler.queue_events((_EventType.Watch, endpoint))

    def read_transport_message(self, origin, message_type):
        return self.event_handler.wait_for_event((_EventType.Transport, origin, message_type))

    def send_packet(self, packet):
        if self.log_packet_level:
            logger.log(self.log_packet_level, "-> %s", packet)
        serialised = packet.serialise_packet()
        self.event_handler.broadcast_event("raw_outbound", serialised)
        self.send_raw(serialised)

    def send_raw(self, message):
        if self.log_protocol_level:
            logger.log(self.log_protocol_level, "-> %s", message.encode('hex'))
        self.transport.send_packet(message)

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
            protocol_caps=0xFFFFFFFFFFFFFFFF
        ))
        self.send_packet(packet)

    @property
    def watch_info(self):
        if self._watch_info is None:
            self.send_packet(WatchVersion(data=WatchVersionRequest()))
            self._watch_info = self.read_from_endpoint(WatchVersion).data
        return self._watch_info

    @property
    def firmware_version(self):
        version = self.watch_info.running.version_tag[1:]
        parts = version.split('-', 1)
        points = [int(x) for x in parts[0].split('.')]
        while len(points) < 3:
            points.append(0)
        if len(parts) == 2:
            suffix = parts[1]
        else:
            suffix = ''
        return FirmwareVersion(*(points + [suffix]))

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
