from __future__ import absolute_import
__author__ = 'katharine'

from enum import IntEnum

from .base import PebblePacket
from .base.types import *

# Time manipulation

__all__ = ["GetTimeRequest", "GetTimeResponse", "SetLocaltime", "SetUTC", "TimeMessage", "AppVersionRequest",
           "AppVersionResponse", "PhoneAppVersion", "FirmwareUpdateStartResponse", "SystemMessage", "BLEControl",
           "WatchVersionRequest", "WatchVersionResponse", "WatchFirmwareVersion", "WatchVersion", "Ping", "Pong",
           "PingPong", "Reset", "Model", "ModelRequest", "ModelResponse", "ModelError", "WatchModel"]


class GetTimeRequest(PebblePacket):
    pass


class GetTimeResponse(PebblePacket):
    time = Uint32()


class SetLocaltime(PebblePacket):
    time = Uint32()


class SetUTC(PebblePacket):
    unix_time = Uint32()
    utc_offset = Int16()
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

    class Type(IntEnum):
        NewFirmwareAvailable = 0x00
        FirmwareUpdateStart = 0x01
        FirmwareUpdateComplete = 0x02
        FirmwareUpdateFailed = 0x03
        FirmwareUpToDate = 0x04
        StopReconnecting = 0x06
        StartReconnecting = 0x07
        MAPDisabled = 0x08
        MAPENabled = 0x09
        FirmwareUpdateStartResponse = 0x0a

    command = Uint8(default=0x00)
    message_type = Uint8(enum=Type)
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

# Firmware/hardware version


class WatchVersionRequest(PebblePacket):
    pass


class WatchFirmwareVersion(PebblePacket):
    timestamp = Uint32()
    version_tag = FixedString(32)
    git_hash = FixedString(8)
    is_recovery = Boolean()
    hardware_platform = Uint8()
    metadata_version = Uint8()


class WatchVersionResponse(PebblePacket):
    running = Embed(WatchFirmwareVersion)
    recovery = Embed(WatchFirmwareVersion)
    bootloader_timestamp = Uint32()
    board = FixedString(9)
    serial = FixedString(12)
    bt_address = BinaryArray(6)
    resource_crc = Uint32()
    resource_timestamp = Uint32()
    language = FixedString(6)
    language_version = Uint16()
    capabilities = Uint64(endianness='<')
    is_unfaithful = Optional(Boolean())


class WatchVersion(PebblePacket):
    class Meta:
        endpoint = 0x10

    command = Uint8()
    data = Union(command, {
        0x00: WatchVersionRequest,
        0x01: WatchVersionResponse,
    })

# Ping, pong.


class Ping(PebblePacket):
    idle = Boolean()


class Pong(PebblePacket):
    pass


class PingPong(PebblePacket):
    class Meta:
        endpoint = 2001

    command = Uint8()
    cookie = Uint32()
    message = Union(command, {
        0: Ping,
        1: Pong,
    })

# Reset


class Reset(PebblePacket):
    class Meta:
        endpoint = 2003
        endianness = '<'

    class Command(IntEnum):
        Reset = 0x00
        DumpCore = 0x01
        FactoryReset = 0x02
        PRF = 0x03

    command = Uint8(enum=Command)

# Watch colour (on top of the former factory/system settings endpoints)


class Model(IntEnum):
    Unknown = 0
    TintinBlack = 1
    TintinWhite = 2
    TintinRed = 3
    TintinOrange = 4
    TintinGrey = 5
    BiancaSilver = 6
    BiancaBlack = 7
    TintinBlue = 8
    TintinGreen = 9
    TintinPink = 10
    SnowyBlack = 11
    SnowyWhite = 12
    SnowyRed = 13
    BobbySilver = 14
    BobbyBlack = 15
    BobbyGold = 16


class ModelRequest(PebblePacket):
    _key = PascalString(default="mfg_color")


class ModelResponse(PebblePacket):
    length = Uint8()
    data = BinaryArray(length=length)


class ModelError(PebblePacket):
    pass


class WatchModel(PebblePacket):
    class Meta:
        endpoint = 5001

    command = Uint8()
    data = Union(command, {
        0x00: ModelRequest,
        0x01: ModelResponse,
        0xff: ModelError,
    })
