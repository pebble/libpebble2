from __future__ import absolute_import
__author__ = 'katharine'

from enum import IntEnum

from .base import PebblePacket
from .base.types import *

__all__ = ["MusicControlPlayPause", "MusicControlPause", "MusicControlPlay", "MusicControlNextTrack",
           "MusicControlPreviousTrack", "MusicControlVolumeUp", "MusicControlVolumeDown", "MusicControlGetCurrentTrack",
           "MusicControlUpdateCurrentTrack", "MusicControl"]


class MusicControlPlayPause(PebblePacket):
    pass


class MusicControlPlay(PebblePacket):
    pass


class MusicControlPause(PebblePacket):
    pass


class MusicControlNextTrack(PebblePacket):
    pass


class MusicControlPreviousTrack(PebblePacket):
    pass


class MusicControlVolumeUp(PebblePacket):
    pass


class MusicControlVolumeDown(PebblePacket):
    pass


class MusicControlGetCurrentTrack(PebblePacket):
    pass


class MusicControlUpdateCurrentTrack(PebblePacket):
    artist = PascalString()
    album = PascalString()
    title = PascalString()
    track_length = Optional(Uint32())
    track_count = Optional(Uint16())
    current_track = Optional(Uint16())


class MusicControlUpdatePlayStateInfo(PebblePacket):
    class State(IntEnum):
        Paused = 0x00
        Playing = 0x01
        Rewinding = 0x02
        Fastforwarding = 0x03
        Unknown = 0x04

    class Shuffle(IntEnum):
        Unknown = 0x00
        Off = 0x01
        On = 0x02

    class Repeat(IntEnum):
        Unknown = 0x00
        Off = 0x01
        One = 0x02
        All = 0x03

    state = Uint8(enum=State)
    track_position = Uint32()
    play_rate = Uint32()
    shuffle = Uint8(enum=Shuffle)
    repeat = Uint8(enum=Repeat)


class MusicControlUpdateVolumeInfo(PebblePacket):
    volume_percent = Uint8()


class MusicControlUpdatePlayerInfo(PebblePacket):
    package = PascalString()
    name = PascalString()


class MusicControl(PebblePacket):
    class Meta:
        endpoint = 0x20
        endianness = '<'

    command = Uint8()
    data = Union(command, {
        0x01: MusicControlPlayPause,
        0x02: MusicControlPause,
        0x03: MusicControlPlay,
        0x04: MusicControlNextTrack,
        0x05: MusicControlPreviousTrack,
        0x06: MusicControlVolumeUp,
        0x07: MusicControlVolumeDown,
        0x08: MusicControlGetCurrentTrack,
        0x10: MusicControlUpdateCurrentTrack,
        0x11: MusicControlUpdatePlayStateInfo,
        0x12: MusicControlUpdateVolumeInfo,
        0x13: MusicControlUpdatePlayerInfo,
    })
