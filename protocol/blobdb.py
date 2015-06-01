__author__ = 'katharine'

from enum import IntEnum

from base import PebblePacket
from base.types import *


class InsertCommand(PebblePacket):
    key_size = Uint8()
    key = BinaryArray(length=key_size)
    value_size = Uint16()
    value = BinaryArray(length=value_size)


class DeleteCommand(PebblePacket):
    key_size = Uint8()
    key = BinaryArray(length=key_size)


class ClearCommand(PebblePacket):
    pass


class BlobCommand(PebblePacket):
    class Meta:
        endpoint = 0xb1db
        register = False
        endianness = '<'

    command = Uint8()
    token = Uint16()
    database = Uint8()
    content = Union(command, {
        0x01: InsertCommand,
        0x04: DeleteCommand,
        0x05: ClearCommand,
    })


class BlobStatus(IntEnum):
    Success = 0x01
    GeneralFailure = 0x02
    InvalidOperation = 0x03
    InvalidDatabaseID = 0x04
    InvalidData = 0x05
    KeyDoesNotExist = 0x06
    DatabaseFull = 0x07
    DataStale = 0x08


class BlobDatabaseID(IntEnum):
    Test = 0
    Pin = 1
    App = 2
    Reminder = 3
    Notification = 4


class BlobResponse(PebblePacket):
    class Meta:
        endpoint = 0xb1db
        endianness = '<'

    token = Uint16()
    response = Uint8(enum=BlobStatus)
