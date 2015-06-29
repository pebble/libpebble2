from __future__ import absolute_import
__author__ = 'katharine'

from enum import IntEnum

from libpebble2.protocol.base import PebblePacket
from libpebble2.protocol.base.types import *


class WebSocketRelayFromWatch(PebblePacket):
    payload = BinaryArray()


class WebSocketRelayToWatch(PebblePacket):
    payload = BinaryArray()


class WebSocketPhoneAppLog(PebblePacket):
    payload = BinaryArray()


class WebSocketPhoneServerLog(PebblePacket):
    payload = BinaryArray()


class WebSocketInstallBundle(PebblePacket):
    pbw = BinaryArray()


class WebSocketInstallStatus(PebblePacket):
    class StatusCode(IntEnum):
        Success = 0x00
        Failed = 0x01
    status = Uint8()


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
    data = PascalString()


class AppConfigCancelled(PebblePacket):
    pass


class WebSocketPhonesimAppConfig(PebblePacket):
    command = Uint8()
    config = Union(command, {
        0x01: AppConfigSetup,
        0x02: AppConfigResponse,
        0x03: AppConfigCancelled,
    })


class WebSocketRelayQemu(PebblePacket):
    protocol = Uint8()
    data = BinaryArray()


class InsertPin(PebblePacket):
    json = BinaryArray()


class DeletePin(PebblePacket):
    uuid = FixedString(36)


class WebSocketTimelinePin(PebblePacket):
    command = Uint8()
    data = Union(command, {
        0x01: InsertPin,
        0x02: DeletePin
    })

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
    0x09: WebSocketProxyAuthenticationResponse
}

endpoints = {v: k for k, v in to_watch.iteritems()}
endpoints.update({v: k for k, v in from_watch.iteritems()})
