from __future__ import absolute_import
__author__ = 'katharine'

from .base import PebblePacket
from .base.types import *

__all__ = ["RequestLogs", "LogMessage", "LogMessageDone", "NoLogMessages", "LogShipping", "AppLogShippingControl",
           "AppLogMessage"]

# Flash log messages


class RequestLogs(PebblePacket):
    generation = Uint8()
    cookie = Uint32()


class LogMessage(PebblePacket):
    cookie = Uint32()
    timestamp = Uint32()
    level = Uint8()
    length = Uint8()
    line = Uint16()
    filename = FixedString(16)
    message = FixedString(length)


class LogMessageDone(PebblePacket):
    cookie = Uint32()


class NoLogMessages(PebblePacket):
    cookie = Uint32()


class LogShipping(PebblePacket):
    class Meta:
        endpoint = 2000

    command = Uint8()
    data = Union(command, {
        0x10: RequestLogs,
        0x80: LogMessage,
        0x81: LogMessageDone,
        0x82: NoLogMessages,
    })

# App log messages


class AppLogShippingControl(PebblePacket):
    class Meta:
        endpoint = 2006
        register = False

    enable = Boolean()


class AppLogMessage(PebblePacket):
    class Meta:
        endpoint = 2006

    uuid = UUID()
    timestamp = Uint32()
    level = Uint8()
    message_length = Uint8()
    line_number = Uint16()
    filename = FixedString(16)
    message = FixedString(message_length)
