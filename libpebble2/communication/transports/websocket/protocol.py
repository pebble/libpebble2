from __future__ import absolute_import
__author__ = 'katharine'

from six import iteritems

from enum import IntEnum

from libpebble2.protocol.base import PebblePacket
from libpebble2.protocol.base.types import *


class WebSocketRelayFromWatch(PebblePacket):
    payload = BinaryArray()


class WebSocketRelayToWatch(PebblePacket):
    payload = BinaryArray()


class WebSocketPhoneAppLog(PebblePacket):
    payload = FixedString()


class WebSocketPhoneServerLog(PebblePacket):
    payload = BinaryArray()


class WebSocketInstallBundle(PebblePacket):
    pbw = BinaryArray()


class WebSocketInstallStatus(PebblePacket):
    class StatusCode(IntEnum):
        Success = 0x00
        Failed = 0x01
    status = Uint32()


class WebSocketPhoneInfoRequest(PebblePacket):
    version = Uint8(default=0x00)


class WebSocketInstallPhoneInfoResponse(PebblePacket):
    payload = BinaryArray()


class WebSocketConnectionStatusUpdate(PebblePacket):
    class StatusCode(IntEnum):
        Connected = 0xff
        Disconnected = 0x00
    status = Uint8()


class WebSocketProxyConnectionStatusUpdate(PebblePacket):
    class StatusCode(IntEnum):
        Connected = 0xff
        Disconnected = 0x00
    status = Uint8()


class WebSocketProxyAuthenticationRequest(PebblePacket):
    token = PascalString()


class WebSocketProxyAuthenticationResponse(PebblePacket):
    class StatusCode(IntEnum):
        Success = 0x00
        Failed = 0x01
    status = Uint8()


class AppConfigSetup(PebblePacket):
    pass


class AppConfigResponse(PebblePacket):
    length = Uint32()
    data = FixedString(length=length)


class AppConfigCancelled(PebblePacket):
    pass


class AppConfigURL(PebblePacket):
    length = Uint32()
    data = FixedString(length=length)


class WebSocketPhonesimAppConfig(PebblePacket):
    command = Uint8()
    config = Union(command, {
        0x01: AppConfigSetup,
        0x02: AppConfigResponse,
        0x03: AppConfigCancelled,
    })


class WebSocketPhonesimConfigResponse(PebblePacket):
    command = Uint8()

    config = Union(command, {
        0x01: AppConfigURL
    })


class WebSocketRelayQemu(PebblePacket):
    protocol = Uint8()
    data = BinaryArray()


class InsertPin(PebblePacket):
    json = FixedString()


class DeletePin(PebblePacket):
    uuid = FixedString(36)


class WebSocketTimelinePin(PebblePacket):
    command = Uint8()
    data = Union(command, {
        0x01: InsertPin,
        0x02: DeletePin
    })


class WebSocketTimelineResponse(PebblePacket):
    class Status(IntEnum):
        Succeeded = 0x00
        Failed = 0x01

    status = Uint8(enum=Status)

to_watch = {
    0x01: WebSocketRelayToWatch,
    0x04: WebSocketInstallBundle,
    0x06: WebSocketPhoneInfoRequest,
    0x09: WebSocketProxyAuthenticationRequest,
    0x0a: WebSocketPhonesimAppConfig,
    0x0b: WebSocketRelayQemu,
    0x0c: WebSocketTimelinePin
}

from_watch = {
    0x00: WebSocketRelayFromWatch,
    0x01: WebSocketRelayToWatch,
    0x02: WebSocketPhoneAppLog,
    0x03: WebSocketPhoneServerLog,
    0x05: WebSocketInstallStatus,
    0x06: WebSocketPhoneInfoRequest,
    0x07: WebSocketConnectionStatusUpdate,
    0x08: WebSocketProxyConnectionStatusUpdate,
    0x09: WebSocketProxyAuthenticationResponse,
    0x0a: WebSocketPhonesimConfigResponse,
    0x0c: WebSocketTimelineResponse,
}

endpoints = {v: k for k, v in iteritems(to_watch)}
endpoints.update({v: k for k, v in iteritems(from_watch)})
