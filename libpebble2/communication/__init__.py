from __future__ import absolute_import

__author__ = 'katharine'

from binascii import hexlify
from collections import namedtuple
from enum import Enum
import logging
import struct
import threading

from .transports import BaseTransport, MessageTargetWatch
from libpebble2.events.threaded import ThreadedEventHandler
from libpebble2.exceptions import PacketDecodeError, ConnectionError, IncompleteMessage
from libpebble2.protocol.base import PebblePacket, PacketType
from libpebble2.protocol.system import (PhoneAppVersion, AppVersionResponse, WatchVersion, WatchVersionRequest,
                                        WatchVersionResponse, WatchModel, ModelRequest, Model)
from libpebble2.util.hardware import PebbleHardware

logger = logging.getLogger("libpebble2.communication")

_EventType = Enum('_EventType', ('Watch', 'Transport'))

FirmwareVersion = namedtuple('FirmwareVersion', ('major', 'minor', 'patch', 'suffix'))
"""
Represents a firmware version, in the format ``major.minor.patch-suffix``.
"""


class PebbleConnection(object):
    """
    PebbleConnection represents the connection to a pebble; all interaction with a pebble goes through it.

    :param transport: The underlying transport layer to communicate with the Pebble.
    :type transport: BaseTransport
    :param log_packet_level: If not None, the log level at which to log decoded messages sent and received.
    :type log_packet_level: int
    :param log_protocol_level: int If not None, the log level at which to log raw messages sent and received.
    :type log_protocol_level: int
    """
    def __init__(self, transport, log_protocol_level=None, log_packet_level=None):
        assert isinstance(transport, BaseTransport)
        self.transport = transport
        self.pending_bytes = b''
        self.event_handler = ThreadedEventHandler()
        self._register_internal_handlers()
        self._watch_info = None
        self._watch_model = None
        self.log_protocol_level = log_protocol_level
        self.log_packet_level = log_packet_level

    def connect(self):
        """
        Synchronously initialises a connection to the Pebble. Once it returns, a valid connection will be open.
        """
        self.transport.connect()

    @property
    def connected(self):
        """
        :return: ``True`` if currently connected to a Pebble; otherwise ``False``.
        """
        return self.transport.connected

    def pump_reader(self):
        """
        Synchronously reads one message from the watch, blocking until a message is available.
        All events caused by the message read will be processed before this method returns.

        .. note::
           You usually don't need to invoke this method manually; instead, see :meth:`run_sync` and :meth:`run_async`.
        """
        origin, message = self.transport.read_packet()
        if isinstance(origin, MessageTargetWatch):
            self._handle_watch_message(message)
        else:
            self._broadcast_transport_message(origin, message)

    def run_sync(self):
        """
        Runs the message loop until the Pebble disconnects. This method will block until the watch disconnects or
        a fatal error occurs.

        For alternatives that don't block forever, see :meth:`pump_reader` and :meth:`run_async`.
        """
        while self.connected:
            try:
                self.pump_reader()
            except PacketDecodeError as e:
                logger.warning("Packet decode failed: %s", e)
            except ConnectionError:
                break

    def run_async(self):
        """
        Spawns a new thread that runs the message loop until the Pebble disconnects.
        ``run_async`` will call :meth:`fetch_watch_info` on your behalf, and block until it receives a response.
        """
        thread = threading.Thread(target=self.run_sync)
        thread.daemon = True
        thread.name = "PebbleConnection"
        thread.start()
        self.fetch_watch_info()

    def _handle_watch_message(self, message):
        """
        Processes a binary message received from the watch and broadcasts the relevant events.

        :param message: A raw message from the watch, without any transport framing.
        :type message: bytes
        """
        if self.log_protocol_level is not None:
            logger.log(self.log_protocol_level, "<- %s", hexlify(message).decode())
        message = self.pending_bytes + message

        while len(message) >= 4:
            try:
                packet, length = PebblePacket.parse_message(message)
            except IncompleteMessage:
                self.pending_bytes = message
                break
            except:
                # At this point we've failed to deconstruct the message via normal means, but we don't want to end
                # up permanently desynced (because we wiped a partial message), nor do we want to get stuck (because
                # we didn't wipe anything). We therefore parse the packet length manually and skip ahead that far.
                # If the expected length is 0, we wipe everything to ensure forward motion (but we are quite probably
                # screwed).
                expected_length, = struct.unpack('!H', message[:2])
                if expected_length == 0:
                    self.pending_bytes = b''
                else:
                    self.pending_bytes = message[expected_length + 4:]
                raise

            self.event_handler.broadcast_event("raw_inbound", message[:length])
            if self.log_packet_level is not None:
                logger.log(self.log_packet_level, "<- %s", packet)
            message = message[length:]
            self.event_handler.broadcast_event((_EventType.Watch, type(packet)), packet)
            if length == 0:
                break
        self.pending_bytes = message

    def _broadcast_transport_message(self, origin, message):
        """
        Broadcasts an event originating from a transport that does not represent a message from the Pebble.

        :param origin: The type of transport responsible for the message.
        :type origin: .MessageTarget
        :param message: The message from the transport
        """
        self.event_handler.broadcast_event((_EventType.Transport, type(origin), type(message)), message)

    def register_transport_endpoint(self, origin, message_type, handler):
        """
        Register a handler for a message received from a transport that does not indicate a message from the connected
        Pebble.

        :param origin: The type of :class:`.MessageTarget` that triggers the message
        :param message_type: The class of the message that is expected.
        :param handler: A callback to be called when a message is received.
        :type handler: callable
        :return: A handle that can be passed to :meth:`unregister_endpoint` to remove the handler.
        """
        return self.event_handler.register_handler((_EventType.Transport, origin, message_type), handler)

    def register_endpoint(self, endpoint, handler):
        """
        Register a handler for a message received from the Pebble.

        :param endpoint: The type of :class:`.PebblePacket` that is being listened for.
        :type endpoint: .PacketType
        :param handler: A callback to be called when a message is received.
        :type handler: callable
        :return: A handle that can be passed to :meth:`unregister_endpoint` to remove the handler.
        """
        return self.event_handler.register_handler((_EventType.Watch, endpoint), handler)

    def register_raw_outbound_handler(self, handler):
        """
        Register a handler for all outgoing messages to be sent to the Pebble. Transport framing is not included.

        :param handler: A callback to be called when any message is received.
        :type handler: callable
        :return: A handle that can be passed to :meth:`unregister_endpoint` to remove the handler.
        """
        return self.event_handler.register_handler("raw_outbound", handler)

    def register_raw_inbound_handler(self, handler):
        """
        Register a handler for all outgoing messages received from the Pebble. Transport framing is not included.
        In most cases you should not need to use this; consider using :meth:`register_endpoint` instead.

        :param handler: A callback to be called when any message is received.
        :type handler: callable
        :return: A handle that can be passed to :meth:`unregister_endpoint` to remove the handler.
        """
        return self.event_handler.register_handler("raw_inbound", handler)

    def unregister_endpoint(self, handle):
        """
        Removes a handler registered by :meth:`register_transport_endpoint`, :meth:`register_endpoint`,
        :meth:`register_raw_outbound_handler` or :meth:`register_raw_inbound_handler`.

        :param handle: A handle returned by the register call to be undone.
        """
        return self.event_handler.unregister_handler(handle)

    def read_from_endpoint(self, endpoint, timeout=10):
        """
        Blocking read from an endpoint. Will block until a message is received, or it times out. Also see
        :meth:`get_endpoint_queue` if you are considering calling this in a loop.

        .. warning::
           Avoid calling this method from an endpoint callback; doing so is likely to lead to deadlock.

        :param endpoint: The endpoint to read from.
        :type endpoint: .PacketType
        :param timeout: The maximum time to wait before raising :exc:`.TimeoutError`.
        :return: The message read from the endpoint; of the same type as passed to ``endpoint``.
        """
        return self.event_handler.wait_for_event((_EventType.Watch, endpoint), timeout=timeout)

    def get_endpoint_queue(self, endpoint):
        """
        Returns a :class:`.BaseEventQueue` from which messages to the given ``endpoint`` can be read.

        This is useful if you need to make sure that you receive all messages to an endpoint, without risking
        dropping some due to time in between :meth:`read_from_endpoint` calls.

        :param endpoint: The endpoint to read from
        :type endpoint: .PacketType
        :return:
        """
        return self.event_handler.queue_events((_EventType.Watch, endpoint))

    def read_transport_message(self, origin, message_type, timeout=10):
        """
        Blocking read of a transport message that does not indicate a message from the Pebble.
        Will block until a message is received, or it times out.

        .. warning::
           Avoid calling this method from an endpoint callback; doing so is likely to lead to deadlock.

        :param origin: The type of :class:`.MessageTarget` that triggers the message.
        :param message_type: The class of the message to read from the transport.
        :param timeout: The maximum time to wait before raising :exc:`.TimeoutError`.
        :return: The object read from the transport; of the same type as passed to ``message_type``.
        """
        return self.event_handler.wait_for_event((_EventType.Transport, origin, message_type), timeout=timeout)

    def send_packet(self, packet):
        """
        Sends a message to the Pebble.

        :param packet: The message to send.
        :type packet: .PebblePacket
        """
        if self.log_packet_level:
            logger.log(self.log_packet_level, "-> %s", packet)
        serialised = packet.serialise_packet()
        self.event_handler.broadcast_event("raw_outbound", serialised)
        self.send_raw(serialised)

    def send_raw(self, message):
        """
        Sends a raw binary message to the Pebble. No processing will be applied, but any transport framing should be
        omitted.

        :param message: The message to send to the pebble.
        :type message: bytes
        """
        if self.log_protocol_level:
            logger.log(self.log_protocol_level, "-> %s", hexlify(message).decode())
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

    def fetch_watch_info(self):
        """
        This method should be called before accessing :attr:`watch_info`, :attr:`firmware_version`
        or :attr:`watch_platform`. Blocks until it has fetched the required information.
        """
        self.send_packet(WatchVersion(data=WatchVersionRequest()))
        self._watch_info = self.read_from_endpoint(WatchVersion).data

    @property
    def watch_info(self):
        """
        Returns information on the connected Pebble, including its firmware version, language, capabilities, etc.

        .. note:
           This is a blocking call if :meth:`fetch_watch_info` has not yet been called, which could lead to deadlock
           if called in an endpoint callback.

        :rtype: .WatchVersionResponse
        """
        if self._watch_info is None:
            self.fetch_watch_info()
        return self._watch_info

    @property
    def firmware_version(self):
        """
        Provides information on the connected Pebble, including its firmware version, language, capabilities, etc.

        .. note:
           This is a blocking call if :meth:`fetch_watch_info` has not yet been called, which could lead to deadlock
           if called in an endpoint callback.

        :rtype: .WatchVersionResponse
        """
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
        """

        :return: The model of the watch.
        :rtype: ~libpebble2.protocol.system.Model
        """
        if self._watch_model is None:
            self.send_packet(WatchModel(data=ModelRequest()))
            info_bytes = self.read_from_endpoint(WatchModel).data.data
            if len(info_bytes) == 4:
                self._watch_model = struct.unpack('>I', info_bytes)
            else:
                self._watch_model = Model.Unknown
        return self._watch_model

    @property
    def watch_platform(self):
        """
        A string naming the platform of the watch ('aplite', 'basalt', 'chalk', or 'unknown').

        .. note:
           This is a blocking call if :meth:`fetch_watch_info` has not yet been called, which could lead to deadlock
           if called in an endpoint callback.

        :rtype: str
        """
        return PebbleHardware.hardware_platform(self.watch_info.running.hardware_platform)
