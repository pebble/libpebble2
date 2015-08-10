from __future__ import absolute_import
__author__ = 'katharine'

from enum import IntEnum

from .base import PebblePacket
from .base.types import *

__all__ = ["DataLoggingReportOpenSessions", "DataLoggingDespoolOpenSession",
           "DataLoggingDespoolSendData", "DataLoggingCloseSession", "DataLoggingACK",
           "DataLoggingNACK", "DataLogging", "DataLoggingTimeout", "DataLoggingEmptySession",
           "DataLoggingGetSendEnableRequest", "DataLoggingGetSendEnableResponse",
           "DataLoggingSetSendEnable"]


class DataLoggingReportOpenSessions(PebblePacket):
    sessions = FixedList(Uint8())


class DataLoggingDespoolOpenSession(PebblePacket):
    class ItemType(IntEnum):
        ByteArray = 0x00
        UnsignedInt = 0x02
        SignedInt = 0x03

    session_id = Uint8()
    app_uuid = UUID()
    timestamp = Uint32()
    log_tag = Uint32()
    data_item_type = Uint8(enum=ItemType)
    data_item_size = Uint16()


class DataLoggingDespoolSendData(PebblePacket):
    session_id = Uint8()
    items_left = Uint32()
    crc = Uint32()
    data = BinaryArray()


class DataLoggingCloseSession(PebblePacket):
    session_id = Uint8()


class DataLoggingACK(PebblePacket):
    session_id = Uint8()


class DataLoggingNACK(PebblePacket):
    session_id = Uint8()


class DataLoggingTimeout(PebblePacket):
    pass

class DataLoggingEmptySession(PebblePacket):
    session_id = Uint8()

class DataLoggingGetSendEnableRequest(PebblePacket):
    pass

class DataLoggingGetSendEnableResponse(PebblePacket):
    enabled = Boolean()

class DataLoggingSetSendEnable(PebblePacket):
    enabled = Boolean()

class DataLogging(PebblePacket):
    class Meta:
        endpoint = 0x1a7a
        endianness = '<'

    command = Uint8()
    data = Union(command, {
        0x01: DataLoggingDespoolOpenSession,
        0x02: DataLoggingDespoolSendData,
        0x03: DataLoggingCloseSession,
        0x84: DataLoggingReportOpenSessions,
        0x85: DataLoggingACK,
        0x86: DataLoggingNACK,
        0x07: DataLoggingTimeout,
        0x88: DataLoggingEmptySession,
        0x89: DataLoggingGetSendEnableRequest,
        0x0A: DataLoggingGetSendEnableResponse,
        0x8B: DataLoggingSetSendEnable,
    })
