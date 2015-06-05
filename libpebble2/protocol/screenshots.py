from __future__ import absolute_import
__author__ = 'katharine'

from enum import IntEnum

from .base import PebblePacket
from .base.types import *

__all__ = ["ScreenshotRequest", "ScreenshotResponse", "ScreenshotHeader"]


class ScreenshotRequest(PebblePacket):
    class Meta:
        endpoint = 8000
        register = False

    _command = Uint8(default=0x00)


class ScreenshotResponse(PebblePacket):
    class Meta:
        endpoint = 8000

    data = BinaryArray()


class ScreenshotHeader(PebblePacket):
    class ResponseCode(IntEnum):
        OK = 0
        MalformedCommand = 1
        OutOfMemory = 2
        AlreadyInProgress = 3

    response_code = Uint8(enum=ResponseCode)
    version = Uint32()
    width = Uint32()
    height = Uint32()
    data = BinaryArray()
