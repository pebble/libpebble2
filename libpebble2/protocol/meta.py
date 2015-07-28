from __future__ import absolute_import
__author__ = 'katharine'

from enum import IntEnum

from .base import PebblePacket
from .base.types import *

__all__ = ["MetaProtocolMessage"]


class MetaProtocolMessage(PebblePacket):
    class Meta:
        endpoint = 0x00

    class Type(IntEnum):
        Disallowed = 0xdd
        Unhandled = 0xdc

    type = Uint8(enum=Type)
    endpoint_id = Uint16()
