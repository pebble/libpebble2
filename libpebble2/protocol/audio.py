from __future__ import absolute_import
__author__ = 'katharine'

from enum import IntEnum

from .base import PebblePacket
from .base.types import *

__all__ = ["AudioCodec", "SpeexEncoderInfo", "StartTransfer", "EncoderFrame", "DataTransfer", "StopTransfer",
           "AudioStream"]


class AudioCodec(IntEnum):
    Speex = 0x01


class SpeexEncoderInfo(PebblePacket):
    version = FixedString(20)
    bitstream_version = Uint8()
    frame_size = Uint16()


class StartTransfer(PebblePacket):
    encoder_id = Uint8(default=AudioCodec.Speex)
    sample_rate = Uint32()
    bit_rate = Uint16()
    extra_info = Union(encoder_id, {
        AudioCodec.Speex: SpeexEncoderInfo,
    })


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

    packet_id = Uint8()
    session_id = Uint16()
    content = Union(packet_id, {
        0x01: StartTransfer,
        0x02: DataTransfer,
        0x03: StopTransfer,
    })