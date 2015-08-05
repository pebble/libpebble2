from __future__ import absolute_import
__author__ = 'katharine'

from .base import PebblePacket
from .base.types import *

__all__ = ["EncoderFrame", "DataTransfer", "StopTransfer", "AudioStream"]


class EncoderFrame(PebblePacket):
    data = BinaryArray()


class DataTransfer(PebblePacket):
    frame_count = Uint8()
    frames = PascalList(EncoderFrame, count=frame_count)


class StopTransfer(PebblePacket):
    pass


class AudioStream(PebblePacket):
    class Meta:
        endpoint = 0x2710
        endianness = '<'

    packet_id = Uint8()
    session_id = Uint16()
    data = Union(packet_id, {
        0x02: DataTransfer,
        0x03: StopTransfer,
    })