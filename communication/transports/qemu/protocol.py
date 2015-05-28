from __future__ import absolute_import
__author__ = 'katharine'

from enum import IntEnum

from protocol.base import PebblePacket
from protocol.base.types import *

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
    direction = Uint8()


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


class QemuVibration(PebblePacket):
    pass


class QemuButton(PebblePacket):
    state = Uint8()


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
        7: QemuVibration,
        8: QemuButton,
    }, length=length)
    footer = Uint16(default=FOOTER_SIGNATURE)
