from __future__ import absolute_import
__author__ = 'katharine'

from enum import IntEnum

from .base import PebblePacket
from .base.types import *

__all__ = ["AppRunState", "AppRunStateStart", "AppRunStateStop", "AppRunStateRequest", "AppMetadata"]

# App run state


class AppRunStateStart(PebblePacket):
    uuid = UUID()


class AppRunStateStop(PebblePacket):
    uuid = UUID()


class AppRunStateRequest(PebblePacket):
    pass


class AppRunState(PebblePacket):
    class Meta:
        endpoint = 0x34
        endianness = '<'

    command = Uint8()
    data = Union(command, {
        0x01: AppRunStateStart,
        0x02: AppRunStateStop,
        0x03: AppRunStateRequest,
    })

# App fetch


class AppFetchRequest(PebblePacket):
    class Meta:
        endpoint = 0x1771
        endianness = '<'

    command = Uint8(default=0x01)
    uuid = UUID()
    app_id = Int32()


class AppFetchStatus(IntEnum):
    Start = 0x01
    Busy = 0x02
    InvalidUUID = 0x03
    NoData = 0x04


class AppFetchResponse(PebblePacket):
    class Meta:
        endpoint = 0x1771
        endianness = '<'
        register = False

    command = Uint8(default=0x01)
    response = Uint8(enum=AppFetchStatus)


class AppMetadata(PebblePacket):
    """
    This represents an entry in the appdb.
    """
    class Meta:
        endianness = '<'

    uuid = UUID()
    flags = Uint32()
    icon = Uint32()
    app_version_major = Uint8()
    app_version_minor = Uint8()
    sdk_version_major = Uint8()
    sdk_version_minor = Uint8()
    app_face_bg_color = Uint8()
    app_face_template_id = Uint8()
    app_name = FixedString(96)
