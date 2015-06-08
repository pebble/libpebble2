from __future__ import absolute_import
__author__ = 'katharine'

from enum import IntEnum

from .base import PebblePacket
from .base.types import *

__all__ = ["LegacyNotification"]


class LegacyNotification(PebblePacket):
    class Meta:
        endpoint = 3000
        endianness = '<'

    class Source(IntEnum):
        Email = 0
        SMS = 1
        Facebook = 2
        Twitter = 3

    type = Uint8(enum=Source)
    sender = PascalString()
    body = PascalString()
    timestamp = PascalString()
    subject = PascalString()
