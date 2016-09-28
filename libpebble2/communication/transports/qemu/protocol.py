from __future__ import absolute_import
__author__ = 'katharine'

from enum import IntEnum

from libpebble2.protocol.base import PebblePacket
from libpebble2.protocol.base.types import *

HEADER_SIGNATURE = 0xFEED
FOOTER_SIGNATURE = 0xBEEF


class QemuSPP(PebblePacket):
    payload = BinaryArray()


class QemuTap(PebblePacket):
    class Axis(IntEnum):
        X = 0
        Y = 1
        Z = 2

    axis = Uint8()
    direction = Int8()


class QemuBluetoothConnection(PebblePacket):
    connected = Boolean()


class QemuCompass(PebblePacket):
    class Calibration(IntEnum):
        Uncalibrated = 0
        Refining = 1
        Complete = 2

    heading = Uint32()
    calibrated = Uint8()


class QemuBattery(PebblePacket):
    percent = Uint8()
    charging = Boolean()


class QemuAccelSample(PebblePacket):
    x = Int16()
    y = Int16()
    z = Int16()


class QemuAccel(PebblePacket):
    count = Uint8()
    samples = FixedList(QemuAccelSample, count=count)


class QemuAccelResponse(PebblePacket):
    remaining_space = Uint16()


class QemuVibration(PebblePacket):
    state = Optional(Boolean())


class QemuButton(PebblePacket):
    class Button(IntEnum):
        Back = 1
        Up = 2
        Select = 4
        Down = 8

    state = Uint8()


class QemuTimeFormat(PebblePacket):
    is_24_hour = Boolean()


class QemuTimelinePeek(PebblePacket):
    enabled = Boolean()


class QemuContentSize(PebblePacket):
    class ContentSize(IntEnum):
        Small = 0
        Medium = 1
        Large = 2
        ExtraLarge = 3

    size = Uint8()


class QemuPacket(PebblePacket):
    signature = Uint16(default=HEADER_SIGNATURE)
    protocol = Uint16()
    length = Uint16()
    data = Union(protocol, {
        1: QemuSPP,
        2: QemuTap,
        3: QemuBluetoothConnection,
        4: QemuCompass,
        5: QemuBattery,
        6: QemuAccel,
        8: QemuButton,
        9: QemuTimeFormat,
        10: QemuTimelinePeek,
        11: QemuContentSize,
    }, length=length)
    footer = Uint16(default=FOOTER_SIGNATURE)


class QemuInboundPacket(PebblePacket):
    signature = Uint16(default=HEADER_SIGNATURE)
    protocol = Uint16()
    length = Uint16()
    data = Union(protocol, {
        1: QemuSPP,
        6: QemuAccelResponse,
        7: QemuVibration,
    }, length=length)
    footer = Uint16(default=FOOTER_SIGNATURE)


class QemuRawPacket(PebblePacket):
    signature = Uint16(default=HEADER_SIGNATURE)
    protocol = Uint16()
    length = Uint16()
    data = BinaryArray(length=length)
    footer = Uint16(default=FOOTER_SIGNATURE)
