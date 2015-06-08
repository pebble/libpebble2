from __future__ import absolute_import
__author__ = 'katharine'

from enum import IntEnum

from .base import PebblePacket
from .base.types import *

__all__ = ["AppMessageTuple", "AppMessagePush", "AppMessageACK", "AppMessageNACK", "AppMessage", "StockAppSetTitle",
           "StockAppSetIcon"]


class AppMessageTuple(PebblePacket):
    class Type(IntEnum):
        ByteArray = 0
        CString = 1
        Uint = 2
        Int = 3

    key = Uint32()
    type = Uint8()
    length = Uint16()
    data = BinaryArray(length=length)


class AppMessagePush(PebblePacket):
    uuid = UUID()
    dictionary = PascalList(AppMessageTuple)


class AppMessageACK(PebblePacket):
    pass


class AppMessageNACK(PebblePacket):
    pass


class AppMessage(PebblePacket):
    class Meta:
        endpoint = 0x30
        endianness = '<'

    command = Uint8()
    transaction_id = Uint8()
    data = Union(command, {
        0x01: AppMessagePush,
        0x03: AppMessageACK,
        0x04: AppMessageNACK,
    })


class StockAppSetTitle(PebblePacket):
    class Meta:
        endpoint = 0x32
        endianness = '<'
        register = False

    class App(IntEnum):
        Sports = 0x00
        Golf = 0x01

    app = Uint8(enum=App)
    title = FixedString(None)


class StockAppSetIcon(PebblePacket):
    class Meta:
        endpoint = 0x32
        endianness = '<'
        register = False

    class App(IntEnum):
        Sports = 0x80
        Gold = 0x81

    app = Uint8(enum=App)
    row_size = Uint16()
    info_flags = Uint16(default=0x1000)
    origin_x = Uint16()
    origin_y = Uint16()
    size_x = Uint16()
    size_y = Uint16()
    image_data = BinaryArray()
