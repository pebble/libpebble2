from __future__ import absolute_import
__author__ = 'katharine'

from enum import IntEnum

from .base import PebblePacket
from .base.types import *

__all__ = ["ObjectType", "PutBytesInstall", "PutBytesInit", "PutBytesAppInit", "PutBytesPut", "PutBytesCommit",
           "PutBytesAbort", "PutBytes", "PutBytesApp", "PutBytesResponse", "GetBytes", "GetBytesCoredumpRequest",
           "GetBytesDataResponse", "GetBytesFileRequest", "GetBytesInfoResponse", "GetBytesFlashRequest",
           "GetBytesUnreadCoredumpRequest"]


class ObjectType(IntEnum):
    Firmware = 0x01
    Recovery = 0x02
    SystemResource = 0x03
    AppResource = 0x04
    AppExecutable = 0x05
    File = 0x06
    Worker = 0x07


class PutBytesInit(PebblePacket):
    object_size = Uint32()
    object_type = Uint8()
    bank = Uint8()
    filename = NullTerminatedString()


class PutBytesAppInit(PebblePacket):
    object_size = Uint32()
    object_type = Uint8()
    app_id = Uint32()


class PutBytesPut(PebblePacket):
    cookie = Uint32()
    payload_size = Uint32()
    payload = BinaryArray(length=payload_size)


class PutBytesCommit(PebblePacket):
    cookie = Uint32()
    object_crc = Uint32()


class PutBytesAbort(PebblePacket):
    cookie = Uint32()


class PutBytesInstall(PebblePacket):
    cookie = Uint32()


class PutBytes(PebblePacket):
    class Meta:
        endpoint = 0xBEEF
        register = False

    command = Uint8()
    data = Union(command, {
        0x01: PutBytesInit,
        0x02: PutBytesPut,
        0x03: PutBytesCommit,
        0x04: PutBytesAbort,
        0x05: PutBytesInstall,
    })


# This is something of a hack: there are two different and fundamentally incompatible init packers,
# which can only be distinguished by the 33rd bit. We rely on the user to know what they're doing.
class PutBytesApp(PebblePacket):
    class Meta:
        endpoint = 0xBEEF
        register = False

    command = Uint8()
    data = Union(command, {
        0x01: PutBytesAppInit,
        0x02: PutBytesPut,
        0x03: PutBytesCommit,
        0x04: PutBytesAbort,
        0x05: PutBytesInstall,
    })


class PutBytesResponse(PebblePacket):
    class Meta:
        endpoint = 0xBEEF

    class Result(IntEnum):
        ACK = 0x01
        NACK = 0x02

    result = Uint8(enum=Result)
    cookie = Uint32()


class GetBytesCoredumpRequest(PebblePacket):
    """Requests a coredump."""
    pass


class GetBytesInfoResponse(PebblePacket):
    class ErrorCode(IntEnum):
        Success = 0x0
        MalformedRequest = 0x1
        InProgress = 0x2
        DoesNotExist = 0x3
        Corrupted = 0x4

    error_code = Uint8(enum=ErrorCode)
    num_bytes = Uint32()


class GetBytesDataResponse(PebblePacket):
    offset = Uint32()
    data = BinaryArray()


class GetBytesFileRequest(PebblePacket):
    """Requests a file. This only works on non-release firmwares."""
    filename = PascalString(null_terminated=True, count_null_terminator=False)


class GetBytesFlashRequest(PebblePacket):
    """Requests a region of flash. This only works on non-release firmwares."""
    offset = Uint32()
    length = Uint32()


class GetBytesUnreadCoredumpRequest(PebblePacket):
    """Requests a coredump, but errors if it has already been read."""
    pass


class GetBytes(PebblePacket):
    class Meta:
        endpoint = 9000

    command = Uint8()
    transaction_id = Uint8()
    message = Union(command, {
        0x00: GetBytesCoredumpRequest,
        0x01: GetBytesInfoResponse,
        0x02: GetBytesDataResponse,
        0x03: GetBytesFileRequest,
        0x04: GetBytesFlashRequest,
        0x05: GetBytesUnreadCoredumpRequest,
    })
