__author__ = 'katharine'

from base import PebblePacket
from base.types import *

# Time manipulation


class GetTimeRequest(PebblePacket):
    pass


class GetTimeResponse(PebblePacket):
    time = Uint32()


class SetLocaltime(PebblePacket):
    time = Uint32()


class SetUTC(PebblePacket):
    unix_time = Uint32()
    utc_offset = Uint16()
    tz_name = PascalString()


class TimeMessage(PebblePacket):
    class Meta:
        endpoint = 0x0b

    kind = Uint8()
    message = Union(kind, {
        0x00: GetTimeRequest,
        0x01: GetTimeResponse,
        0x02: SetLocaltime,
        0x03: SetUTC
    })

# Phone app version


class AppVersionRequest(PebblePacket):
    pass


class AppVersionResponse(PebblePacket):
    protocol_version = Uint32()  # Unused as of v3.0
    session_caps = Uint32()  # Unused as of v3.0
    platform_flags = Uint32()
    response_version = Uint8(default=2)
    major_version = Uint8()
    minor_version = Uint8()
    bugfix_version = Uint8()
    protocol_caps = Uint64()


class PhoneAppVersion(PebblePacket):
    class Meta:
        endpoint = 0x11

    kind = Uint8()
    message = Union(kind, {
        0x00: AppVersionRequest,
        0x01: AppVersionResponse,
    })

# System message


class FirmwareUpdateStartResponse(PebblePacket):
    response = Uint8()


class SystemMessage(PebblePacket):
    class Meta:
        endpoint = 0x12
        endianness = '<'

    kind = Uint8(default=0x00)
    message_type = Uint8()
    extra_data = Union(message_type, {
        0x0a: FirmwareUpdateStartResponse,
    }, accept_missing=True)

# BLE control


class BLEControl(PebblePacket):
    class Meta:
        endpoint = 0x33
        endianness = '<'

    opcode = Uint8(default=0x4)
    discoverable = Boolean()
    duration = Uint16()

# Log messages


class LogShippingControl(PebblePacket):
    class Meta:
        endpoint = 0x07D0
        register = False

    kind = Uint8(default=0x00)
    level = Uint8()


class LogMessage(PebblePacket):
    class Meta:
        endpoint = 0x07D0

    timestamp = Uint32()
    level = Uint8()
    message_length = Uint8()
    line_number = Uint16()
    filename = FixedString(16)
    message = FixedString(message_length)
