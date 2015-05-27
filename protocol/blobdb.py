__author__ = 'katharine'

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
    command = Uint8()
    token = Uint16()
    database = Uint8()
    content = Union(command, {
        0x01: InsertCommand,
        0x04: DeleteCommand,
        0x05: ClearCommand,
    })
