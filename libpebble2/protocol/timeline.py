from __future__ import absolute_import
__author__ = 'katharine'

"""
This file is special in that it actually contains definitions of
blobdb blob formats rather than pebble protocol messages.
"""

from enum import IntEnum

from .base import PebblePacket
from .base.types import *

__all__ = ["TimelineAttribute", "TimelineAction", "TimelineItem"]


class TimelineAttribute(PebblePacket):
    # This makes no attempt to handle serialisation, since that's delegated to a JSON
    # file that is out of scope for this serialiser.
    attribute_id = Uint8()
    length = Uint16()
    content = BinaryArray(length=length)


class TimelineAction(PebblePacket):
    class Type(IntEnum):
        AncsDismiss = 0x01
        Generic = 0x02
        Response = 0x03
        Dismiss = 0x04
        HTTP = 0x05
        Snooze = 0x06
        OpenWatchapp = 0x07
        Empty = 0x08

    action_id = Uint8()
    type = Uint8(enum=Type)
    attribute_count = Uint8()
    attributes = FixedList(TimelineAttribute, count=attribute_count)


class TimelineItem(PebblePacket):
    class Meta:
        endianness = '<'

    class Type(IntEnum):
        Notification = 1
        Pin = 2
        Reminder = 3

    item_id = UUID()
    parent_id = UUID()
    timestamp = Uint32()
    duration = Uint16()
    type = Uint8(enum=Type)
    flags = Uint16()
    layout = Uint8()
    data_length = Uint16()
    attribute_count = Uint8()
    action_count = Uint8()
    attributes = FixedList(TimelineAttribute, count=attribute_count, length=data_length)
    actions = FixedList(TimelineAction, count=action_count, length=data_length)
